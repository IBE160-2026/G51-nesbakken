# Product Brief: {Jaunt}

## Executive Summary

Jaunt is a web application that builds a a walking route based on three main inputs: where you are, how long you have, and optionally what kind of walk you want. It delivers a route on a map with real stops in a suggested order, with something to discover, notice or learn about or do along the way. The Jaunt is built around the users total available time, including both walking and time spent at stops. 

The problem Jaunt solves is not a shortage of information about places around us. That information already exists in maps, articles, heritage registers and other sources, but often arrives as individual places or lists rather than a walk you can actually take. Turning it into a route means deciding where to go, what is worth seeing, in what order, and whether the whole experience fits the time available. For a casual walk, that planning can require more effort than the walk is worth.

Jaunt does that planning for the user, turning available time into a purposeful walk that can be followed directly on a map. Rather than always producing a route, it prioritises real and relevant stops and can suggest a different topic or shorter walk when there is not enough nearby to create a worthwhile Jaunt. The goal is to make “have a Jaunt” an easy answer when you have some spare time, need a break, or simply want something worth walking for.

## The Problem

Going for walk is an easy way to get outside, take a break or fill some spare time. However, without a destination or a purpose, getting out the door can get surpringly difficult. In familiar areas, walks can also become repetitive, you have the same street, same distance and little reason to pay attention to what exists around you. 

Finding a more interesting walk may require planning. Deciding where to go, search for things in the area, and work out a sensible route in a suitable timeframe are all components that eats up disposable time. For someone with 30-60 minutes available, the planning takes up enough effort that it either becomes the usual route or it does not happen at all. 

On another side of this, being in an area unfamiliar to you, might lead to the same problems. There may be plenty of accessible recommendations, maps and information, but turning it into a walk starting where you are, fits your available time and gives you a worthwhile experience along the way requires effort. 

The problem is therefore, how do we turn available time, into a purposeful walk. 

## The Solution

Jaunt turns the time someone has available into a purposeful walk from where they are. The user provides a starting point and how much time they have, and can optionally provide information on what kind of walk the are interested in. Jaunt then creates a route that fits within the total time available, including both walking and time spent at stops. 

Instead of just routing between nearby attractions, Jaunt gives the walk a purpose through relevant places, stories, details or small activities along the way. A user might choose a history, architechture or public-art Jaunt, or let Jaunt choose based on what is available nearby. 

By default, a Jaunt returns the user to the starting point, while a point-to-point walk can also be supported. The proposed route and stops are shown before the user sets off, allowing them to decide whether the Jaunt is worth taking. 

Jaunt should only create a route when there is enough suitable material nearby to make the requested walk worthwhile. If a chosen topic cannot support a good Jaunt within available time, it should instead suggest a shorter route or a different topic rather than filling the rout with weak or invented stops. 

## What Makes This Different

Jaunt is designed specifically around the walk itself rather than the search for places. Instead of returning a list of nearby recommendations or requiring the user to assmeble a route, it uses starting point, available time and optional interest into an experience that can be followed on a map. 

The available time represents the outing, this includes the time to stop and engage with places along the route. Each stop gives the user a reason for being there through relevant context, stories or prompts. Eventually this can be experienced through audio as well as text. 

Jaunt also prioritises quality of the walk over always returning a result. In cases where there is not enough suitable information for the requested topic and time, it can suggest a different or shorter Jaunt rather than creating weak or fabricated stops. 

In the long term, Jaunt could combine reliable public information with knowledge contributed by people who know an area (local legends). Allowing small local details and places that rarely appear in conventional guides to become part of future Jaunts. 

## Who This Serves

Primary user: Someone who likes walking, or wants to walk more, but misses somewhere specific to go. The may have some time to kill, need a break or just simple wishes to go outside without spending time or mental capacity on deciding a route or destination. Jaunt attempts to give familiar surroundings enough novelty and purpose to make the walk feel more worthwhile. 

Secondary user: Someone in an unfamiliar area who wants to explore on foot without researching attractions and constructing their own route. Instead of trying to see "everything" they want a walk that fits their available time and helps them notice or learn something about the area they are already in. 

## Success Criteria

The first version of Jaunt is successful if it is able to reliably turn a users starting point, available time and optional topic into a walk that is practical to complete and gives user a reason to get out and explore. Success will be avaluated threough real-world testing of generated Jaunts. Testers should be able to follow the route from their phone, complete the full experience reasonable close to their stated time, and encounter real and relevant stops with context along the way. 

Testing should include both developer and external users, with feedback focused on wether the route was easy to follow, the stops felt worthwhile and how actual completion time was compared to the estimated time. Lastly, and most importantly, whether the walk felt worth getting out the door for. 

A successful prototype should demonstrate that users would consider using Jaunt again when thet want to go for a walk but do not have somewhere to go. 

## Scope

The first version (V1) will focus on proving the core experience: That a purposeful and engaging walk can be created from a users location available time and interests without requiring them to plan the route themselves. 

V1 aims to support: 
* A starting point entered by the user, with current location supported is feasible. 
* A total available time for the Jaunt 
* A small number of topics, initially history, architecture and public art, alongside a "surprise me" option. 
* A generated walking route displayed on an interactive walking map. 
* A default loopthat returns user to their starting point, with point-to-point routes supported if achievable within project. 
* A small number of real stops selected because they contribute something relevant to chosen topic. 
* Short, source-based context or stories for each stop, available as text. 
* The ability to have this content read out loud if feasible within project. 
* An alternative suggestion when the requested time/topic/location cannot support a worthwhile Jaunt. 

The first version does not need to work equally well everywhere. Development and testing will focus on defined area where sufficient source information is available. 

## Vision

Jaunt could develop from a simple route generator into a way of discovering the places around you through walking. Rather than relying only on conventional attractions or manually curated walking tours, Jaunt could combine reliable public information with local knowledge to create many different walks around the same neighbourhood. 

Over time, users could contribute places, details and stories they think are worth noticing. Jaunt could use these contributions alongside other sources to create new routes. This would allow knowledge that normally only lives with people who know an area to become a part of someone elses walk. 

The long-term goal is for "have a Jaunt" to become an easy answer to having some spare time, needing a break, wanting to get outside, or wanting to explore somewhere unfamiliar. Just tell Jaunt how much time you have, and it gives you something worth walking for. 
