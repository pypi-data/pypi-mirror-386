# Tcg-Research-Desk
Various tools for analysing trading card game tournament results. 
Behind Urza's Research Desk - a web app to display and interrogate win rates and aggregate archetypes from magic the gathering.
[See the app here!](https://arckaynine.github.io/Urzas-Research-Desk/)

## Dev Notes

### V1 Requirements
There is some major functionality/things to investigate before making this more widely available:

TODO
- Bug: "Unholy Annex // Ritual Chamber" and "Unholy Annex && Ritual Chamber" both show up in the data.
- Bug: "(BRO 16)", "(DAR 213)", etc. show up in data for Pioneer.
- Bug: All decks have valid WRs - Fix globbing in get_tournament_files (related to broader problem of format id from file).
- Split into preprocess and postprocess pip imports (mainly an sklearn thing).
- Remove pre-modern and premodern from modern
- Docco/how to.

DONE (Pending testing)
-

DONE
- Lock light/dark mode.
- Fix selection default info.
- Double check interaction between selection and individual card analysis - 0 coppies now show up.
- Lock plots in place.
- Tables can't be edited.
- Automated updates from MTGODecklistCache.
- Card images onhover.
- Fix selection updates.
- How do mixed format events (PTs) look in the data? - Just constructed rounds show up.
- Mishra's Research Desk artist credit.
- Tooltip hover not covered by tabs.
- Fix tooltip in general. - Breaks when you go straight from one to another.
- Win rate scatter legend placement.
- Archetype bundles.
- Reset all selections option.
- Handle for when no selected decks play 0 coppies of any card.
- Process_data also saves a minimized AtomicCards.json
- Process_data to also save opening clusters
- Hover broken on flip cards in HTML.
- HTML hover in top left corner.
- Scale down.
- Confidence on matrix.
- Loading messages

### V2 Goals
- Temporal analysis.
- (Option to) Remove mirrors.
- Add tooltip to cards in html vis.
- Show last data read time
- Easy time select on format boundaries (new set release, bans).
- Filter to specific event.
- Card search on mobile.
- Plotting accessibility features (colours and fill/marker styles, not just colour).
- Highlight cards of interest (extreme wr variation by qtty within archetypes).
- Strip out as much data as possible. (do some of the tourney/player/archetype merging in preprocess, only keep card data needed for vis).