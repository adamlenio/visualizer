Subject: Casambi Visualizer — where it's headed, and some API architecture questions

Hi Michael,

A quick update and, more importantly, a few forward-looking questions I'd value your guidance on.

**Where things stand.** The interactive Office visualizer has come a long way. It's now rendering each luminaire individually in full RGB, so the demo can control every fixture — and any group — to any color and level, photorealistically, in the browser. It mirrors the current Casambi app UI closely (Luminaires, Gallery, Scenes, Settings), and there's a live build deployed. In effect it's a photoreal, interactive version of the app's Gallery feature.

**Where I want to take it.** The goal is a public web experience where anyone — a specifier, an end client, a curious visitor — can land on the site, pick a space that resembles their own (Office first, then Church, Library, Gallery, and more), and try the full Casambi app experience on it: build groups, create scenes, tune color and CCT, set schedules, run animations. On top of that I want to layer guided tutorials over the rendered rooms, so it doubles as interactive training. And finally, I want it to act as a lead-generation tool that routes interested visitors to Casambi's reps.

To make that real, the central question is how much of it should run on the actual Casambi API versus logic I simulate on my side. I'd rather lean on the real platform wherever it makes sense, which raises a few things:

1. **Virtual / hardware-less networks.** Does the API support a network that exists with no physical devices — one a web app could authenticate to and drive purely as a simulation? That's the cleanest way to give visitors an authentic experience with no gateway or fixtures involved.

2. **Multi-user isolation.** A public demo means many people using it at once, each expecting their own independent room to control without stepping on each other. How do you envision that — ephemeral per-visitor networks, per-session state, or something else? A single shared network obviously won't work for concurrent public users.

3. **Scaling to many networks / API contexts.** Between multiple environments and potentially per-visitor sessions, I'd be provisioning and driving a lot of networks under one developer account. What are the practical limits, provisioning paths, and rate limits I should design around?

4. **Credential architecture.** I want to make sure I'm using the right auth path. I have a developer API key, and I've been sorting out the distinction between the local bridge login and the cloud account the REST session endpoint expects — a quick confirmation of the intended flow for cloud/virtual networks would save me some guesswork.

5. **Partnership fit.** Given the training and lead-gen angles, is this something Casambi would want to actively support or collaborate on — as a marketing, education, and rep-enablement tool? I'd love to build it in a direction that's genuinely useful to your team.

If you're open to it, a short call to talk through the virtual-network and multi-user pieces would unblock the most important architectural decisions. Happy to send the live demo link ahead of time so you can click through it.

Thanks as always for your guidance.

Best,
Adam
