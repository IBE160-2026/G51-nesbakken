V4
# Product Brief: Jaunt

## Executive Summary

Jaunt is a web application that turns a user's available time into a purposeful walking experience. The user enters a starting location, chooses how much time they have, and may select an interest such as history, architecture, or public art. Jaunt then creates a walking route with real and relevant stops in a suggested order, giving the user something to discover, notice, or learn about along the way.

The available time represents the complete outing, including both walking and time spent at stops. By default, a Jaunt returns the user to their starting point.

Jaunt uses AI to select relevant, source-supported stops based on the user’s topic and time limit, while a mapping service calculates the walking route and duration. AI also creates short stories, facts, tasks, or observation prompts based on source material associated with each stop.

If the requested topic, location, or duration cannot support a worthwhile route, Jaunt should suggest a different topic or shorter walk rather than inventing places or including weak and irrelevant stops.

## The Problem

Going for a walk is an accessible way to get outside, take a break, or fill spare time. However, without a destination or purpose, getting out the door can be surprisingly difficult. In familiar areas, walks can become repetitive, while creating a more interesting walk requires finding relevant places, arranging them into a sensible route, and determining whether it fits the available time.

The same problem exists in unfamiliar areas. Maps and recommendation services may provide many individual attractions, but they do not necessarily turn them into a coherent walk that starts nearby, fits a specific amount of time, and gives the walker something meaningful to discover.

The central problem is therefore:

> How can available time be turned into a purposeful walk without requiring the user to plan it themselves?

## Proposed Solution

The user provides three main inputs:

- A starting point
- The total time available
- An optional topic or "surprise me"

Jaunt uses a source-supported dataset and AI to select a small group of relevant stops for the chosen topic. A mapping service calculates a practical route between them, while estimated walking time and an allowance for time at each stop are checked against the user’s total time limit. If necessary, the selection is adjusted until a suitable route is found or Jaunt determines that the request cannot be fulfilled.

The route is displayed on an interactive map, with short AI-generated content for each stop based on its associated source material. Because Jaunt is intended to be used while walking, the application is designed mobile-first.

The result is not simply a list of nearby attractions. It is an ordered walking experience designed around the user's available time and interests.

## Intended Users

The primary user is someone who wants to walk but does not have a particular destination in mind. They may have time to fill, need a break, or want to go outside without using time and mental effort to plan a route. Jaunt gives familiar surroundings novelty and purpose.

A secondary user is someone in an unfamiliar area who wants to explore on foot without researching attractions and constructing their own route. Instead of trying to see everything, they want a manageable walk that fits their available time and helps them notice or learn something about where they already are.

## What Makes Jaunt Different

Existing map and recommendation services are generally designed to find individual places or provide directions to a destination already chosen by the user. Jaunt instead begins with the walk itself, using the user’s starting location, available time, and interests to select and organise relevant stops.

The time limit applies to the complete outing, including time spent at stops. Jaunt also prioritises trustworthy and relevant results over always generating an answer: an honest alternative is more useful than a route containing fabricated, inaccessible, or unrelated stops.

## V1 Scope

The first version will focus on a defined inner-Sydney test area covering the CBD and nearby neighbourhoods that can be tested locally, including Chippendale, Redfern, Surry Hills, Glebe, Erskineville, and Newtown. This area has sufficient public information about historical places, architecture, and public art, and its bounded scope makes it possible to verify stops and sources, evaluate the AI-generated content, and complete real-world testing of route quality and timing.

V1 will include:

- Selection of a starting point on the map
- Selection of total available time
- History, architecture, public art, and "surprise me" topics
- AI-assisted selection of relevant stops from collected, source-supported place data
- A loop route that returns to the starting point
- A small number of real stops in a suggested order
- An interactive map displaying the route and stops
- Estimated walking time plus an allowance for time at stops
- Short AI-generated content based on source material
- Source information for the content
- A useful alternative when no suitable route can be created

The prototype does not need to provide the same quality of results outside the selected area. It will use an automatically collected and processed catalogue of candidate places and sources for that area, allowing the catalogue to grow without places being entered manually.

Possible extensions, if time permits, include using the device's current location, point-to-point routes, and reading stop content aloud. User accounts, worldwide coverage, user-contributed places, and social features are outside the initial scope.

## Data and Important Decisions

**Data in:**

- Starting location
- Available time
- Selected topic
- Source-supported place information and coordinates
- Source material associated with each place
- Walking routes and travel-time estimates

**Data out:**

- An ordered walking route
- Estimated walking and stop time
- Selected stops displayed on a map
- Short AI-generated stories, facts, or prompts
- References to the source material
- Alternative suggestions when a route cannot be created

Important development decisions include how candidate places are collected and verified, how AI determines their relevance to a topic, how the route and time constraints are checked, and how generated descriptions are kept consistent with their sources.

## Success Criteria

Jaunt will be evaluated through developer testing and external user testing in inner Sydney. A successful prototype should demonstrate that:

- A user can select a starting point, available time, and optional topic and receive a suitable result.
- The route can be viewed and followed from a phone.
- The complete walk can be finished reasonably close to the requested time.
- Displayed stops are real and relevant to the selected topic.
- AI-generated content is consistent with the supplied source material.
- The application responds honestly when it cannot create a suitable route.
- Testers feel that the walk was worth taking and would consider using Jaunt again.

Testing will compare estimated and actual completion times and gather feedback about route clarity, stop relevance, trustworthiness, and the overall experience.

## Vision

In the future, Jaunt could support more locations, topics, route types, and audio experiences. It could also allow people with local knowledge to contribute overlooked places and stories, subject to suitable verification.

The long-term goal is for "have a Jaunt" to become an easy answer when someone has spare time, needs a break, wants to go outside, or wants to explore somewhere unfamiliar. Tell Jaunt how much time you have, and it gives you something worth walking for.
