## Cloze Overlapper Add-on for Anki

Facilitates **memorizing enumerations**, lists, or any other type of sequential information by breaking the sequence up into cards where each item serves as the context cue for the next:

![](screenshots/demo1.gif)


### Table of Contents

<!-- MarkdownTOC -->

- [Background](#background)
- [The Add-on](#the-add-on)
- [Documentation](#documentation)
- [Help](#help)
- [Credits and License](#credits-and-license)

<!-- /MarkdownTOC -->


### Background
 
Memorizing lists and enumerations has always been a particularly difficult part of studying flashcards. Good flashcards follow the **minimum information principle**, where the content of each card is reduced to its essentials; but sequential information can not always be sensibly chunked down to its constituents. Because each item of a sequence builds on the next, methods like grouping or categorizing are usually not a viable option.

One of the [common recommendations](https://www.supermemo.com/en/articles/20rules#Enumerations) for cases like this is to create **informationally overlapping flashcards**, where the answer to each card serves as a prompt for the next, e.g.:

    List items:           A        B        C        D
    Resulting cards:  ->A | A -> B | B -> C | C -> D | D->

While this can be highly effective, creating cards like these manually can also be an enormous **time-sink**. For that reason students will usually opt against implementing this method in their own studying routine, even though it might result in a much better retention rate in the long run. 

### The Add-on

This is where *Cloze Overlapper* comes in: Instead of writing a flashcard for each pair of list items, you simply type in the sequence in its entirety and **let the add-on generate the cards** for you. The cards will only provide you with the context you need to recall each item at hand. This will result in a **chain of overlapping associations** between each sequence node, potentially strengthening your memory and improving your recall performance.

Both the number of context cues and the length of each prompt can be **freely customized** on a per-note basis, allowing you to adjust Cloze Overlapper for whatever purpose you see fit:

![](screenshots/demo2.gif)

Cards generated with this add-on are fully compatible with **all platforms**, AnkiMobile and AnkiDroid included:

![](screenshots/platforms.png)



### Documentation

The use of the add-on is documented in the [Wiki section](https://github.com/Glutanimate/cloze-overlapper/wiki) and a [series of video tutorials on YouTube](https://www.youtube.com/playlist?list=PL3MozITKTz5Y9owI163AJMYqKwhFrTKcT).



### Help

Please use the [official forum thread](https://anki.tenderapp.com/discussions/add-ons/9407-cloze-overlapper-official-thread) for all support requests and questions.



### Credits and License

I would like to extend my heartfelt thanks to everyone who has helped with testing, provided suggestions, or contributed in any other way!

I'd also like to thank:

- [Piotr Wozniak](https://www.supermemo.com/english/company/wozniak.htm) for laying the theoretical groundwork for overlapping cloze deletions with his [20 rules of formulating knowledge](https://www.supermemo.com/en/articles/20rules)
- [Soren Bjornstad](https://github.com/sobjornstad) for giving me the inspiration for this add-on with his project [AnkiLPCG](https://github.com/sobjornstad/AnkiLPCG), back when it was still a standalone module

*Cloze Overlapper* is *Copyright © 2016-2017 [Aristotelis P.](https://github.com/Glutanimate)*

This add-on is licensed under the [GNU AGPL v3](https://www.gnu.org/licenses/agpl.html).
