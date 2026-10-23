"""Preference discovery contract, using only mocked provider boundaries."""
import json
import unittest
from unittest.mock import Mock, patch

import ai
import planner
from app import app


def place(i):
    return dict(id=str(i), name=f'Place {i}', latitude=-33.8983 + i*.00001,
                longitude=151.1793, status='ready', topics=['history'],
                source_excerpt='Documented place')


class DiscoveryTests(unittest.TestCase):
    def test_invalid_ids_retry_then_service_error(self):
        for ids in (['0', '0'], ['unknown', '0'], ['0'], ['0','1','2'], None):
            with self.subTest(ids=ids), patch('ai._call_openai', return_value=json.dumps({'candidate_ids': ids})) as provider:
                with self.assertRaises(ai.AiExhaustedError):
                    ai.discover_candidates([place(i) for i in range(3)], 'history', .37, 2)
                self.assertEqual(provider.call_count, 2)
                self.assertIn('Previous response failed:', provider.call_args.args[0])
                self.assertIn('unique offered IDs', provider.call_args.args[0])
                self.assertLessEqual(len(provider.call_args.args[0]), ai.MAX_DISCOVERY_PROMPT_CHARS)

    def test_transient_discovery_failure_retries_once(self):
        with patch('ai._call_openai', side_effect=[ai.AiSelectionError('timeout'), '{"candidate_ids":["0","1"]}']) as provider:
            self.assertEqual(ai.discover_candidates([place(i) for i in range(3)], 'history', 1, 2), ['0','1'])
        self.assertEqual(provider.call_count,2)

    def test_fatal_errors_do_not_retry(self):
        with patch('ai._call_openai', side_effect=ai.AiFatalError('quota')) as provider:
            with self.assertRaises(ai.AiFatalError):
                ai.discover_candidates([place(i) for i in range(3)], 'history', 0, 2)
            self.assertEqual(provider.call_count, 1)

    def test_compact_prompt_context_and_exact_preference(self):
        candidates = [dict(place(i), name='x'*140, source_title='y'*180, source_excerpt='z'*400) for i in range(3)]
        with patch('ai._call_openai', return_value='{"candidate_ids":["2","1"]}') as provider:
            self.assertEqual(ai.discover_candidates(candidates, 'history', .37, 2), ['2','1'])
        prompt = json.loads(provider.call_args.args[0])
        self.assertEqual(prompt['preference'], .37)
        self.assertIn('Sydney', prompt['location_context'])
        self.assertEqual(prompt['candidates'][1]['latitude'], candidates[1]['latitude'])
        self.assertEqual(prompt['candidates'][1]['longitude'], candidates[1]['longitude'])
        self.assertEqual(len(prompt['candidates'][0]['source_excerpt']), 320)
        self.assertIn('unknown does not mean hidden', provider.call_args.kwargs['system_prompt'])
        self.assertIn('general knowledge', ai.build_prompt([], 'history', 60))

    def test_limits_fail_before_provider(self):
        for candidates in ([place(i) for i in range(201)], [dict(place(i), id='x'*10000+str(i)) for i in range(13)]):
            with patch('ai._call_openai') as provider, self.assertRaises(ai.AiExhaustedError):
                ai.discover_candidates(candidates, 'history', 0, 12)
            provider.assert_not_called()

    def run_plan(self, responses, matrices=None, retained=None, preference=0, excluded=None):
        candidates = [place(i) for i in range(14)]
        calls = []
        def provider(prompt, **kwargs):
            details = json.loads(prompt) if kwargs else json.JSONDecoder().raw_decode(prompt.split('\n\n',1)[1])[0]
            calls.append(details)
            if kwargs:
                return json.dumps({'candidate_ids': [str(i) for i in range(13, 1, -1) if str(i) not in (retained or []) + (excluded or [])][:12-len(retained or [])]})
            return json.dumps({'selected_option': next(responses), 'none_suitable_reason': 'no relevant option'})
        matrix = [[0 if i==j else 60 for j in range(13)] for i in range(13)]
        with patch('planner.load_ready_places', return_value=candidates), patch('planner.fetch_duration_matrix', side_effect=matrices or [matrix,matrix]) as routing, patch('ai._call_openai', side_effect=provider):
            result = planner.plan_route(-33.8983,151.1793,'history',30,preference=preference, excluded_ids=excluded,
                                        retained_ids=retained, replacement_mode=retained is not None)
        return result,calls,routing

    def test_outside_nearest_landmark_reaches_real_feasible_menu(self):
        result,calls,routing = self.run_plan(iter(['option_1']))
        self.assertTrue(result['feasible'])
        self.assertEqual(len(calls[0]['candidates']),14)
        self.assertIn('13', {s['id'] for o in calls[1]['options'] for s in o['stops']})
        self.assertEqual({s['id'] for s in calls[1]['options'][0]['stops']}, {'13','12'})
        self.assertLessEqual(len(calls[1]['options']),15)
        self.assertEqual({s['id'] for o in calls[1]['options'] for s in o['stops']}, {str(i) for i in range(2,14)})
        self.assertEqual(len(routing.call_args.args[0]),13)
        self.assertEqual(routing.call_count,1)

    def test_ordinary_candidates_accepted_at_all_preferences_with_recovery(self):
        # These generic fixtures carry no fame labels; assertions concern transport
        # and orchestration, not the live model's qualitative judgement.
        for preference in (0, .5, 1, .37):
            for responses in (['option_1'], ['none_suitable','option_1']):
                with self.subTest(preference=preference, responses=responses):
                    result,calls,routing = self.run_plan(iter(responses), preference=preference)
                    self.assertTrue(result['feasible'])
                    self.assertEqual(routing.call_count,len(responses))
                    self.assertTrue(all(c['preference']==preference for c in calls))
                    self.assertEqual(result['attempts'],len(responses))
                    if len(responses)==2:
                        self.assertEqual([entry['shortlist'] for entry in result['attempts_log']], ['discovery','nearest_recovery'])
                    else:
                        self.assertNotIn('shortlist',result['attempts_log'][0])

    def test_exclusions_and_retention_survive_both_attempts(self):
        result,calls,routing=self.run_plan(iter(['none_suitable','option_1']),retained=['1'],excluded=['2'])
        self.assertNotIn('2', {p['id'] for p in calls[0]['candidates']})
        for call in routing.call_args_list:
            self.assertNotIn((place(2)['latitude'],place(2)['longitude']),call.args[0])
            self.assertIn((place(1)['latitude'],place(1)['longitude']),call.args[0])
        for details in calls[1:]:
            for option in details['options']:
                ids={p['id'] for p in option['stops']}
                self.assertNotIn('2',ids)
                self.assertIn('1',ids)
        self.assertNotIn('2',result['selected_ids'])
        self.assertIn('1',result['selected_ids'])
        self.assertEqual(routing.call_count,2)

    def test_discovery_schema_and_system_reach_http_transport(self):
        response=Mock()
        response.json.return_value={'choices':[{'message':{'content':'{"candidate_ids":["1","0"]}'}}]}
        with patch.dict('os.environ',{'OPENAI_API_KEY':'fixture-key','OPENAI_MODEL':'fixture-model'}), patch('ai.requests.post',return_value=response) as post:
            ids=ai.discover_candidates([place(i) for i in range(3)],'history',.37,2)
        self.assertEqual(ids,['1','0'])
        payload=post.call_args.kwargs['json']
        self.assertEqual(payload['response_format']['json_schema'],ai.DISCOVERY_SCHEMA)
        self.assertEqual(payload['messages'][0],{'role':'system','content':ai.DISCOVERY_SYSTEM_PROMPT})

    def test_no_combo_recovers_nearest(self):
        blocked = [[0 if i==j else None for j in range(13)] for i in range(13)]
        valid = [[0 if i==j else 60 for j in range(13)] for i in range(13)]
        result,calls,routing = self.run_plan(iter(['option_1']),[blocked,valid])
        self.assertTrue(result['feasible'])
        self.assertEqual(routing.call_count,2)

    def test_retained_only_recovers_and_keeps_retention(self):
        result,calls,routing = self.run_plan(iter(['none_suitable','option_1']),retained=['1'])
        self.assertEqual(result['replacement_outcome'],'replacement_found')
        self.assertIn('1', result['selected_ids'])
        self.assertEqual(routing.call_count,2)

    def test_small_pool_skips_discovery_and_filters_hard_constraints(self):
        candidates = [place(0), place(1), dict(place(2), status='rejected'),
                      dict(place(3), topics=['public_art']), dict(place(4), latitude=None)]
        matrix = [[0 if i==j else 60 for j in range(3)] for i in range(3)]
        with patch('planner.load_ready_places', return_value=candidates), patch('ai.discover_candidates') as discovery, patch('planner.fetch_duration_matrix', return_value=matrix), patch('ai.select_stops', return_value={'selected_option':'option_1','none_suitable_reason':''}):
            result=planner.plan_route(-33.8983,151.1793,'history',30,preference=1)
        self.assertTrue(result['feasible'])
        self.assertEqual(set(result['selected_ids']), {'0','1'})
        discovery.assert_not_called()
        wild=planner.collect_eligible_candidates(-33.8983,151.1793,'surprise_me',places=candidates,excluded_ids=['0'])
        self.assertEqual({p['id'] for p in wild}, {'1','3'})

    def test_technical_selection_failure_never_recovers(self):
        with patch('planner.load_ready_places',return_value=[place(i) for i in range(14)]), patch('ai.discover_candidates',return_value=[str(i) for i in range(2,14)]), patch('planner.fetch_duration_matrix', return_value=[[0 if i==j else 60 for j in range(13)] for i in range(13)]) as routing, patch('ai.select_stops',side_effect=ai.AiFatalError('quota')):
            with self.assertRaises(ai.AiFatalError):
                planner.plan_route(-33.8983,151.1793,'history',30)
        self.assertEqual(routing.call_count,1)

    def test_identical_membership_does_not_repeat_matrix(self):
        with patch('planner.load_ready_places',return_value=[place(i) for i in range(14)]), patch('ai.discover_candidates',return_value=[str(i) for i in reversed(range(12))]), patch('planner.fetch_duration_matrix', return_value=[[0 if i==j else 60 for j in range(13)] for i in range(13)]) as routing, patch('ai.select_stops',return_value={'selected_option':'none_suitable','none_suitable_reason':'not relevant'}):
            result=planner.plan_route(-33.8983,151.1793,'history',30)
        self.assertFalse(result['feasible'])
        self.assertEqual(routing.call_count,1)

    def test_recovery_stops_after_second_honest_rejection(self):
        result,calls,routing=self.run_plan(iter(['none_suitable','none_suitable']))
        self.assertFalse(result['feasible'])
        self.assertIn('candidates checked', result['reason'])
        self.assertEqual(routing.call_count,2)

    def test_five_place_pool_ranks_every_id_and_offers_top_pair(self):
        candidates=[place(i) for i in range(5)]
        matrix=[[0 if i==j else 60 for j in range(6)] for i in range(6)]
        prompts=[]
        def provider(prompt, **kwargs):
            details=json.loads(prompt) if kwargs else json.JSONDecoder().raw_decode(prompt.split('\n\n',1)[1])[0]
            prompts.append(details)
            return json.dumps({'candidate_ids':['4','3','2','1','0']} if kwargs else {'selected_option':'option_1','none_suitable_reason':''})
        with patch('planner.load_ready_places',return_value=candidates), patch('planner.fetch_duration_matrix',return_value=matrix), patch('ai._call_openai',side_effect=provider):
            result=planner.plan_route(-33.8983,151.1793,'history',60,preference=0)
        self.assertEqual(prompts[0]['count'],5)
        self.assertEqual({p['id'] for p in prompts[0]['candidates']},{str(i) for i in range(5)})
        self.assertEqual(set(result['selected_ids']),{'4','3'})
        self.assertEqual({s['id'] for option in prompts[1]['options'] for s in option['stops']},{str(i) for i in range(5)})
        self.assertLessEqual(len(prompts[1]['options']),15)

    def test_oversized_pool_is_api_503(self):
        with app.test_client() as client, patch('planner.load_ready_places',return_value=[place(i) for i in range(201)]), patch('ai._call_openai') as provider:
            response=client.post('/api/plan',json={'start_lat':-33.8983,'start_lon':151.1793,'topic':'history','requested_minutes':30})
        self.assertEqual(response.status_code,503)
        provider.assert_not_called()
