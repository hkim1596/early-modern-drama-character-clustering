# Audit — character_documents

## Build summary

- rows in: 9745   __crowd__ dropped: 107   rows out: 9638
- masks  person: 95300  place: 18502  nation: 9493  deity: 11330
- tcp repairs: 6163   stage directions removed: 3546
- mask_rate  median: 0.0141  max: 0.2500  rows with zero masks: 1054

## Sample

Random 40 rows + 5 highest-repair + 5 highest-mask-rate. `BEFORE` is speech_text, `AFTER` is speech_text_embedding.

### A11954.19 — BATES (169 words)

masks: person 1, place 1, nation 1, deity 0 | tcp repairs 0, stage dirs 0 | mask_rate 0.0178

**BEFORE**

> I think it be: but we have no great cause to desire the approach of day. He hath not told his thought to the King? He may show what outward courage he will: but I believe, as cold a Night as it's, he could wish him self in Thames up to the Neck; and so I would he were, and I by him, at all adventures, so we were quit here. Then I would he were here alone; so should he be sure to be ransomed, and a many poor men's lives saved. I, or more then we should seek after; for we know enough, if we know we are the Kings Subjects: if his Cause be wrong, our obedience to the King wipes the Crime of it out

**AFTER**

> I think it be: but we have no great cause to desire the approach of day. He hath not told his thought to the King? He may show what outward courage he will: but I believe, as cold a Night as it's, he could wish him self in that place up to the Neck; and so I would he were, and I by him, at all adventures, so we were quit here. Then I would he were here alone; so should he be sure to be ransomed, and a many poor men's lives saved. I, or more then we should seek after; for we know enough, if we know we are the Kings Subjects: if his Cause be wrong, our obedience to the King wipes the Crime of it

---

### A06185 — ADAM (2962 words)

masks: person 8, place 3, nation 2, deity 2 | tcp repairs 1, stage dirs 0 | mask_rate 0.0051

**BEFORE**

> Why what shall we have this paltry Smith with us? Why slave I am a gentleman Villain were it not that we go to be merry, pier should presently quit thy opproprious terms. Oh Peter, Peter, put up thy sword I prithee heartily into thy barred, hold in your rapier, for though I have not a long reach have a short hitter. Nay then gentlemen stay me, for my begins to rise against him, for mark the words a paltry O horrible sentence, thou hast in these words I will stand libeled against all the found horses, whole horses, soar Coursers, Curtals, Jades, Cuts, Hackneys, and Mare upon my friend, in their

**AFTER**

> Why what shall we have this paltry Smith with us? Why slave I am a gentleman Villain were it not that we go to be merry, pier should presently quit thy opproprious terms. Oh someone, put up thy sword I prithee heartily into thy barred, hold in your rapier, for though I have not a long reach have a short hitter. Nay then gentlemen stay me, for my begins to rise against him, for mark the words a paltry O horrible sentence, thou hast in these words I will stand libeled against all the found horses, whole horses, soar Coursers, Curtals, Jades, Cuts, Hackneys, and Mare upon my friend, in their defe

---

### A12129 — AURELIA (1535 words)

masks: person 3, place 2, nation 0, deity 0 | tcp repairs 0, stage dirs 4 | mask_rate 0.0033

**BEFORE**

> No Sir, I am the daughter of that Gentleman, No sun I'll assure you. Prithee do not mind him. You shall command the duty of a daughter, But I hope mother, you will give me leave To love before I marry I have yet No argument of his affection, But what you please to bring me it becomes not My modesty to court him, and give up My heart before I hear him say, he means To meet and entertain it. Love, forgive me this excuse, my heart is fixed, I find another written here. You may believe my sister, she n'er speaks But by direction of her heart. You're bountiful in character. Nothing, as much as he h

**AFTER**

> No Sir, I am the daughter of that Gentleman, No sun I'll assure you. Prithee do not mind him. You shall command the duty of a daughter, But I hope mother, you will give me leave To love before I marry I have yet No argument of his affection, But what you please to bring me it becomes not My modesty to court him, and give up My heart before I hear him say, he means To meet and entertain it. Love, forgive me this excuse, my heart is fixed, I find another written here. You may believe my sister, she n'er speaks But by direction of her heart. You're bountiful in character. Nothing, as much as he h

---

### A02128 — MARGARET (2210 words)

masks: person 53, place 10, nation 3, deity 9 | tcp repairs 2, stage dirs 0 | mask_rate 0.0339

**BEFORE**

> Thomas, maids when they come to see the fair Count not to make a cope for dearth of hay, When we have turned our butter to the salt, And set our cheese upon the racks. Then let our father's prize it as they please, We Country sluts of merry Fressingfield, Come to buy needless noughts to make us fine, And look that youngmen should be frank this day, And court us with such fairings as they can. Phœbus is blithe and, frolic, looks from heaven, As when he courted lovely Semele: Swearing the Pedlars shall have empty packs, If that fair weather may make chapmen buy. This is a faring gentle sir indee

**AFTER**

> Someone, maids when they come to see the fair Count not to make a cope for dearth of hay, When we have turned our butter to the salt, And set our cheese upon the racks. Then let our father's prize it as they please, We Country sluts of merry Fressingfield, Come to buy needless noughts to make us fine, And look that youngmen should be frank this day, And court us with such fairings as they can. The god is blithe and, frolic, looks from heaven, As when he courted lovely the god: Swearing the Pedlars shall have empty packs, If that fair weather may make chapmen buy. This is a faring gentle sir in

---

### A03217 — SHERIFF (156 words)

masks: person 4, place 1, nation 0, deity 0 | tcp repairs 0, stage dirs 0 | mask_rate 0.0321

**BEFORE**

> 'Tis a strange Comet M. Hobson, My time to my remembrance hath not seen A sighed so wonderful. M. Worser. Nowell, To judge of these things your experience Exceeds ours, what do you hold of it? For I have herd that Meteors in the air, Of lesser form, less wonderful then these, Rather foretell of danger's imminent, Then flatter us wish future happiness. Which is already done, being fourscore households, Were sold for 478. pound. The plot is also plained at the Cities charges, And we in name of the whole Citizens, Do come to give you full possession Of this our purchase, whereon to built a Burse,

**AFTER**

> 'Tis a strange Comet M. Someone, My time to my remembrance hath not seen A sighed so wonderful. Someone. Someone, To judge of these things your experience Exceeds ours, what do you hold of it? For I have herd that Meteors in the air, Of lesser form, less wonderful then these, Rather foretell of danger's imminent, Then flatter us wish future happiness. Which is already done, being fourscore households, Were sold for 478. pound. The plot is also plained at the Cities charges, And we in name of the whole Citizens, Do come to give you full possession Of this our purchase, whereon to built a Burse,

---

### A20100 — MOLL (744 words)

masks: person 2, place 0, nation 1, deity 0 | tcp repairs 0, stage dirs 0 | mask_rate 0.004

**BEFORE**

> Lady. You see what a hell I live in, I am resolved to leave him. This madness shows very well. The Gentleman you spoke of hath often solici ted my love, and hath received from me most chased denials. Have you indeed? I have no counsel in your voiag , neither shall you have any in mine. Sleep, Jas quietly as a Client having great business with Lawyers. Whats the forepart? That it was my hard fortune, being so well brought up, having so great a portion to my marriage, to match so vnlucki lie? Why my husband and his whole credit is not worth my ap parell, well, I shall undergo a strange repo to i

**AFTER**

> Lady. You see what a hell I live in, I am resolved to leave him. This madness shows very well. The Gentleman you spoke of hath often solici ted my love, and hath received from me most chased denials. Have you indeed? I have no counsel in your voiag , neither shall you have any in mine. Sleep, Jas quietly as a Client having great business with Lawyers. Whats the forepart? That it was my hard fortune, being so well brought up, having so great a portion to my marriage, to match so vnlucki lie? Why my husband and his whole credit is not worth my ap parell, well, I shall undergo a strange repo to i

---

### A04206 — RAGAU (2190 words)

masks: person 47, place 0, nation 0, deity 0 | tcp repairs 3, stage dirs 0 | mask_rate 0.0215

**BEFORE**

> I have been here this half hour sir waiting for you. You have no cause, that I know, any fault to find: Except that we disease our tent and neighbours all With rising over early eke day when you call. Nay I speak of your neighbours being men honest, That labour all the day, and would feign be at rest: Whom with blowing your Horn you disease all abouts. And I speak of Rebecca your mother, our dame. And I speak of your good father, old Isaac. I blame not dogs to take it, if they may it geat: But as for my part, they could have pardie, A small relevauit of that that you give me. They may run ligh

**AFTER**

> I have been here this half hour sir waiting for you. You have no cause, that I know, any fault to find: Except that we disease our tent and neighbours all With rising over early eke day when you call. Nay I speak of your neighbours being men honest, That labour all the day, and would feign be at rest: Whom with blowing your Horn you disease all abouts. And I speak of someone your mother, our dame. And I speak of your good father, old someone. I blame not dogs to take it, if they may it geat: But as for my part, they could have pardie, A small relevauit of that that you give me. They may run li

---

### A11966 — LADY PERCY (425 words)

masks: person 2, place 0, nation 1, deity 0 | tcp repairs 0, stage dirs 1 | mask_rate 0.0071

**BEFORE**

> Oh my good Lord, why are you thus alone? For what offence have I this fortnight been A banished woman from my Harries bed? Tell me sweet Lord, what is't that takes from thee Thy stomach, pleasure, and thy golden sleep? Why dost thou bend thine eyes upon the earth? And start so often when thou I st alone? Why hast thou lost the fresh blood in thy cheeks? And given my treasures and my rights of thee To thick eyed musing, and cursed melancholy? In thy faint slumbers I by thee have watched, And herd the murmur, tales of iron wars, Speak terms of manage to thy bounding steed, Cry courage to the fie

**AFTER**

> Oh my good Lord, why are you thus alone? For what offence have I this fortnight been A banished woman from my Harries bed? Tell me sweet Lord, what is't that takes from thee Thy stomach, pleasure, and thy golden sleep? Why dost thou bend thine eyes upon the earth? And start so often when thou I st alone? Why hast thou lost the fresh blood in thy cheeks? And given my treasures and my rights of thee To thick eyed musing, and cursed melancholy? In thy faint slumbers I by thee have watched, And herd the murmur, tales of iron wars, Speak terms of manage to thy bounding steed, Cry courage to the fie

---

### B00230 — CHRONOMASTIX (441 words)

masks: person 0, place 0, nation 0, deity 0 | tcp repairs 0, stage dirs 0 | mask_rate 0.0

**BEFORE**

> What? what? my friends, will not this room receive? When have I walked the streets, but happy he That had the finger first to point at me, Prentice, or Journeyman! The shop does know it! The unlettered Clarke! Mayor and minor Poet! The Sempster hath sat still as I passed by, And dropped her needle! Fishwives stayed their cry! The Boy with buttons, and the Basket wench To vent their wares, into my works do trench! A pudding-wife, that would despise the Times, Hath vtterd' frequent pen' worths, through my rhymes, And, with them, dived into the Chambermaid, And she unto her Lady hath conveyed The

**AFTER**

> What? what? my friends, will not this room receive? When have I walked the streets, but happy he That had the finger first to point at me, Prentice, or Journeyman! The shop does know it! The unlettered Clarke! Mayor and minor Poet! The Sempster hath sat still as I passed by, And dropped her needle! Fishwives stayed their cry! The Boy with buttons, and the Basket wench To vent their wares, into my works do trench! A pudding-wife, that would despise the Times, Hath vtterd' frequent pen' worths, through my rhymes, And, with them, dived into the Chambermaid, And she unto her Lady hath conveyed The

---

### A02800 — WALGRAVE (1309 words)

masks: person 25, place 4, nation 5, deity 0 | tcp repairs 0, stage dirs 0 | mask_rate 0.026

**BEFORE**

> A match say you? a mischief 'twill as soon: Should I can scarce begin to speak to her, But I am interrupted by her father. Would, what say you? and then put over his snout, Able to shadow Powles, it is so great. Well, 'tis no matter, sirrs, this is his House, Knock for the Churl bid him bring out his Daughter; I'll, sbloud I will, though I be hanged for it, Whom, Anthony our friend? Say man, how fares our Loves? How does Mathea ? Can she love Ned ? how does she Like my suit? Will old Pisaro take me for his Son; For I thank God, he kindly takes our Lands, Swearing, Good Gentlemen you shall not 

**AFTER**

> A match say you? a mischief 'twill as soon: Should I can scarce begin to speak to her, But I am interrupted by her father. Would, what say you? and then put over his snout, Able to shadow Powles, it is so great. Well, 'tis no matter, sirrs, this is his House, Knock for the Churl bid him bring out his Daughter; I'll, sbloud I will, though I be hanged for it, Whom, someone our friend? Say man, how fares our Loves? How does someone ? Can she love Ned ? how does she Like my suit? Will old someone take me for his Son; For I thank God, he kindly takes our Lands, Swearing, Good Gentlemen you shall no

---

### A19757 — SECOND OFFICER (61 words)

masks: person 0, place 0, nation 0, deity 0 | tcp repairs 0, stage dirs 0 | mask_rate 0.0

**BEFORE**

> We have nothing to charge you with about your page It is the wounding your wife with and unlawful weapon. The fellow raves, he thinks men in office have no thing to do but to give him justice, you must first be punished and then talk of justice when you have cause. Nay then you are mad indeed, away with him.

**AFTER**

> We have nothing to charge you with about your page It is the wounding your wife with and unlawful weapon. The fellow raves, he thinks men in office have no thing to do but to give him justice, you must first be punished and then talk of justice when you have cause. Nay then you are mad indeed, away with him.

---

### A07326 — MATHO (120 words)

masks: person 0, place 0, nation 0, deity 0 | tcp repairs 0, stage dirs 0 | mask_rate 0.0

**BEFORE**

> Health to my Sovereign. Your Highness may command my service In that, or any thing lies in my power. If it lie within the compass of my knowledge, I will resolve your Highness presently. I have my Liege, and every circumstance That can be thought on in the business. He must die for it, the case is plain, Unless your grace will grant his pardon. It cannot be my Liege, the Statutes is plain. I dare not undertake it, could it be done, Idem go as far as any man would do. I do beseech your Highness to excuse me, I cannot do more then your laws will let me, Nor falsify my knowledge nor my conscience

**AFTER**

> Health to my Sovereign. Your Highness may command my service In that, or any thing lies in my power. If it lie within the compass of my knowledge, I will resolve your Highness presently. I have my Liege, and every circumstance That can be thought on in the business. He must die for it, the case is plain, Unless your grace will grant his pardon. It cannot be my Liege, the Statutes is plain. I dare not undertake it, could it be done, Idem go as far as any man would do. I do beseech your Highness to excuse me, I cannot do more then your laws will let me, Nor falsify my knowledge nor my conscience

---

### A01840 — LORD (87 words)

masks: person 1, place 0, nation 0, deity 0 | tcp repairs 0, stage dirs 0 | mask_rate 0.0115

**BEFORE**

> Look out, me thought I herd one cry out murder, Some voice I am sure did disturb the court, It was Misanders voice me thought that cried, Spies him dead. And see he's slain; one whom the Kings esteem Did rank among the best; there are the murderers, Fellows, how durst you thus abuse the court? Go, haste to'th' Kings tell him the men be here. Yes; and here comes his Majesty in person, My gracious Sovereign, these two be the men, Which have confessed the deed:

**AFTER**

> Look out, me thought I herd one cry out murder, Some voice I am sure did disturb the court, It was someone's voice me thought that cried, Spies him dead. And see he's slain; one whom the Kings esteem Did rank among the best; there are the murderers, Fellows, how durst you thus abuse the court? Go, haste to'th' Kings tell him the men be here. Yes; and here comes his Majesty in person, My gracious Sovereign, these two be the men, Which have confessed the deed:

---

### A03404 — RODERICK (1072 words)

masks: person 19, place 3, nation 1, deity 0 | tcp repairs 2, stage dirs 3 | mask_rate 0.0215

**BEFORE**

> Ten thousand men of Orleans I come maund, And those are bravely marshalled on the plain, Ready to be commanded by your Highness, Pembroke, you are too plain in your discourse. Princes, you ask, you know not what your selves. Why, they ask peace, and we are set for war. Zounds, here's a truce made up by miracle. What stratagem? More then poison two: But you, my Lord, forget your self too far; Know you to whom you have disclosed your heart? The deer friend of Lews the French King. Peter de Lions is your Lordship's servant, A boon companion, and a lusty Knave: He is in love with Bellamiraes maid,

**AFTER**

> Ten thousand men of that place I come maund, And those are bravely marshalled on the plain, Ready to be commanded by your Highness, someone, you are too plain in your discourse. Princes, you ask, you know not what your selves. Why, they ask peace, and we are set for war. Zounds, here's a truce made up by miracle. What stratagem? More then poison two: But you, my Lord, forget your self too far; Know you to whom you have disclosed your heart? The deer friend of someone's the foreign King. Someone de Lions is your Lordship's servant, A boon companion, and a lusty Knave: He is in love with Bellami

---

### A14193 — ANNOT (214 words)

masks: person 6, place 1, nation 0, deity 0 | tcp repairs 0, stage dirs 0 | mask_rate 0.0327

**BEFORE**

> By Cock and well sowed, my good Tibet Talk apace. And how does our old beldame here, Mage Mumblecrust? To make us poor girls shent to his is small gain. Let all these matters pass, and we three sing a song, So shall we pleasantly both the time beguile now, And eke dispatch all our works ere we can tell how. Have we done singing since? then will I in again, Here I found you, and here I leave both twain. To me tr lie is he welcome. And why not Annot Alyface as as she Then our pretty new come man will look to be one. Perchance he can not sing. Yet get e not all, we will go with you both. And have

**AFTER**

> By Cock and well sowed, my good someone apace. And how does our old beldame here, Mage someone? To make us poor girls shent to his is small gain. Let all these matters pass, and we three sing a song, So shall we pleasantly both the time beguile now, And eke dispatch all our works ere we can tell how. Have we done singing since? then will I in again, Here I found you, and here I leave both twain. To me tr lie is he welcome. And why not someone as as she Then our pretty new come man will look to be one. Perchance he can not sing. Yet get e not all, we will go with you both. And have partly of yo

---

### A12954 — MALINDO (1404 words)

masks: person 3, place 1, nation 0, deity 4 | tcp repairs 1, stage dirs 0 | mask_rate 0.0057

**BEFORE**

> Make me acknowledge this thy love sincere, Bring thy magnanimous courage into act; Oh be my agent, reconcile the doubts Which do possess my intellectual sense. The Statesmen are my sole Antigonists, They do seduce and steal away the King. Keep his heroic bounty for themselves; They do detain his nature punctually, Make him (deluded) parsimonious, Erect who pleases their magnificence, Who them displease, the king must frown upon: They do entomb the silly wretch alive, Make him as dead, to eminent designs, Which they approve not; then revive his will, To adventure such, as none approve but they 

**AFTER**

> Make me acknowledge this thy love sincere, Bring thy magnanimous courage into act; Oh be my agent, reconcile the doubts Which do possess my intellectual sense. The Statesmen are my sole Antigonists, They do seduce and steal away the King. Keep his heroic bounty for themselves; They do detain his nature punctually, Make him (deluded) parsimonious, Erect who pleases their magnificence, Who them displease, the king must frown upon: They do entomb the silly wretch alive, Make him as dead, to eminent designs, Which they approve not; then revive his will, To adventure such, as none approve but they 

---

### A03205 — GANYMEDE (107 words)

masks: person 0, place 0, nation 0, deity 1 | tcp repairs 0, stage dirs 0 | mask_rate 0.0093

**BEFORE**

> Why that's no gift: I am no prisoner, And therefore owe no ransom, having breath, Know I have vowed to yield to none save death. Now speakest thou Like the noblest of my foes. I love him best, whose strokes can loudest found. Not as prisoner. I am conquered both by Arms and Courtesy. Those filial duties you so much forget We come to teach you. Royal Kings to arms, Give Ganymede the onset of this battle, That being a son knows how to lecture them, And chastise their transgressions. Why that's my honour, when alone I stand Gainst thee and all the forces of thy land.

**AFTER**

> Why that's no gift: I am no prisoner, And therefore owe no ransom, having breath, Know I have vowed to yield to none save death. Now speakest thou Like the noblest of my foes. I love him best, whose strokes can loudest found. Not as prisoner. I am conquered both by Arms and Courtesy. Those filial duties you so much forget We come to teach you. Royal Kings to arms, Give the god the onset of this battle, That being a son knows how to lecture them, And chastise their transgressions. Why that's my honour, when alone I stand Gainst thee and all the forces of thy land.

---

### A07970 — 2 BLADE (90 words)

masks: person 1, place 0, nation 0, deity 0 | tcp repairs 0, stage dirs 0 | mask_rate 0.0111

**BEFORE**

> The Master of the house is the master of the house; but we will master both him and you unless you deliver. Your servant sweet Lady. Come come, you must sweet Lady. Correct us! nay then along Lady. One draws & stands at the door, while the other carry her away. I bleed too. Baffled and hurt! we may revenge it sir. Will you so sir? we are for you. As he offers to draw, the Blades come in and bind him. He speaks ends out of a puppet play.

**AFTER**

> The Master of the house is the master of the house; but we will master both him and you unless you deliver. Your servant sweet Lady. Come come, you must sweet Lady. Correct us! nay then along Lady. One draws & stands at the door, while the other carry her away. I bleed too. Baffled and hurt! we may revenge it sir. Will you so sir? we are for you. As he offers to draw, the someone's come in and bind him. He speaks ends out of a puppet play.

---

### A03496 — PHLEGMATICO (492 words)

masks: person 11, place 0, nation 1, deity 0 | tcp repairs 5, stage dirs 0 | mask_rate 0.0244

**BEFORE**

> Before love most Meteorological Tobacco! He takes Tobac continued, drinks, and then spawles. (again) Pure Indian! (again) Not a lot Sophisticated (a gain) A Tobacco-pipe is the Chimney of perpetual Hospi talitie (again) Before love most Metropolitan Tobacco! He drinks a gain and Sings, while Logicus, and Causidicus privately with draw to the side of the Stage. TObacco's a Musician And in a Pipe delights; It descends in a Close, Through the Organ of the nose, With a Relish that inviteth. This makes me sing So ho, ho, So ho ho boys, Ho boys found J loudly; Earth never did breed Such a jovial wee

**AFTER**

> Before love most Meteorological Tobacco! He takes someone continued, drinks, and then spawles. (again) Pure foreign! (again) Not a lot Sophisticated (a gain) A Tobacco-pipe is the Chimney of perpetual Hospi talitie (again) Before love most Metropolitan Tobacco! He drinks a gain and Sings, while someone privately with draw to the side of the Stage. TObacco's a Musician And in a Pipe delights; It descends in a Close, Through the Organ of the nose, With a Relish that inviteth. This makes me sing So ho, ho, So ho ho boys, Ho boys found J loudly; Earth never did breed Such a jovial weed Whereof to 

---

### A68278.1 — THOMAS (169 words)

masks: person 6, place 2, nation 0, deity 0 | tcp repairs 0, stage dirs 0 | mask_rate 0.0473

**BEFORE**

> Benedicamus Domini, was ever such and injury. Sweet S. Withhold of thy lenity, defend us from extremity, And hear us for S. Charity, oppressed with austerity. In nomini Domini, make I my homily, Gentle Gentility griene not the Clergy. A pardon, Oparce, Saint France's for mercy, Shall shield thee from nightspells and dreaming of devils, If thou wilt forgive me, and never more grieve me, With fasting and praying, and Hail Marry saying. From black Purgatory a penance right sorry. Friar Thomas will warm you, It shall never harm you. O I am vndun, fair Alice the Nun Hath took up her rest in the Abb

**AFTER**

> Someone, was ever such and injury. Someone of thy lenity, defend us from extremity, And hear us for S. Charity, oppressed with austerity. In nomini Domini, make I my homily, Gentle Gentility griene not the Clergy. A pardon, that place, Saint that place's for mercy, Shall shield thee from nightspells and dreaming of devils, If thou wilt forgive me, and never more grieve me, With fasting and praying, and someone saying. From black Purgatory a penance right sorry. Friar someone will warm you, It shall never harm you. O I am vndun, fair someone the Nun Hath took up her rest in the Abbots chest, Sa

---

### A13360 — DUKE (494 words)

masks: person 6, place 5, nation 1, deity 0 | tcp repairs 0, stage dirs 0 | mask_rate 0.0243

**BEFORE**

> Thus all alone from Cestus am I come, And left my princely court and nobl train, To come to Athens, and in this disguise, To see what course my son Aurelius takes. But stay, heres some it may be travels thither, Good sir can you direct me the way to Athens? Fair lovely maid, young and affable, More clear of hew and far more beautiful Then precious Sardonix or purple rocks, Of Amithests or glistering Hiasinth, More amiable far then is the plain, Where glistering Cepherus in silver boures, Gazeth upon the Giant Andromede, Sweet Kate entertain this lovely woman. I am glad sir that you would be so

**AFTER**

> Thus all alone from Cestus am I come, And left my princely court and nobl train, To come to that place, and in this disguise, To see what course my son someone takes. But stay, heres some it may be travels thither, Good sir can you direct me the way to that place? Fair lovely maid, young and affable, More clear of hew and far more beautiful Then precious that place or purple rocks, Of foreigners or glistering Hiasinth, More amiable far then is the plain, Where glistering Cepherus in silver boures, someone upon the Giant Andromede, Sweet someone entertain this lovely woman. I am glad sir that y

---

### A02827 — IMPLEMENT (2142 words)

masks: person 10, place 5, nation 3, deity 1 | tcp repairs 0, stage dirs 1 | mask_rate 0.0089

**BEFORE**

> REnowned Father of fashions, Count of cour tesies, Marquess of modern motions, Duke of debonair deportments, Chief Justice of ges icum lations. I have it, Comptroller of Conges, Compactor of Cringes, Fea Framer of jan phrases. Dainty? I tell thee, Novice, we have store of this plumporridge at our house every day. (little else.) That trumpet could speak Persian well, I can hardly hit upon them in the original. Varletto, p one, manigoldo. Indoctrinate of young Nobility. Accompli r of Kings Courts, chief engineer of cap and knee. clock-keeper of , and finally, ingrosser of all sailable, available

**AFTER**

> REnowned Father of fashions, Count of cour tesies, Marquess of modern motions, Duke of debonair deportments, Chief Justice of ges icum lations. I have it, Comptroller of Conges, Compactor of Cringes, Fea Framer of jan phrases. Dainty? I tell thee, someone, we have store of this plumporridge at our house every day. (little else.) That trumpet could speak foreign well, I can hardly hit upon them in the original. Someone, p one, manigoldo. Indoctrinate of young Nobility. Accompli r of Kings Courts, chief engineer of cap and knee. clock-keeper of , and finally, ingrosser of all sailable, available

---

### A72473.1 — CUTTING (189 words)

masks: person 0, place 0, nation 0, deity 0 | tcp repairs 0, stage dirs 0 | mask_rate 0.0

**BEFORE**

> They fallen to their vam pours, a gain. No, Sir, but he may tire, if it please him. No matter who told him so, so long as he knows. 'Slight, I'll pardon him, an'I list, whosoever says nay to't. No, he must not Like it at all, Sir, there you are i'the wrong. Nay, then he both must, and will Like it, Sir, for all you. Yes, in some sense you may have reason, Sir. It's true, thou hast no sense indeed. Nay, it is no sufficient vapour, neither, I deny that. It may be a sweet vapour. By your leave, it may, Sir. Mind? why, here's no man minds you, Sir, They drink again. nor any thing else. Yes, Sir, e

**AFTER**

> They fallen to their vam pours, a gain. No, Sir, but he may tire, if it please him. No matter who told him so, so long as he knows. 'Slight, I'll pardon him, an'I list, whosoever says nay to't. No, he must not Like it at all, Sir, there you are i'the wrong. Nay, then he both must, and will Like it, Sir, for all you. Yes, in some sense you may have reason, Sir. It's true, thou hast no sense indeed. Nay, it is no sufficient vapour, neither, I deny that. It may be a sweet vapour. By your leave, it may, Sir. Mind? why, here's no man minds you, Sir, They drink again. nor any thing else. Yes, Sir, e

---

### A04638 — RACHEL (288 words)

masks: person 8, place 0, nation 0, deity 0 | tcp repairs 0, stage dirs 0 | mask_rate 0.0278

**BEFORE**

> Gone abroad my Lord: I but I fear heel presently return, Are you now going my most honoured Lord? No is your presence nothing, I shall want that, and wanting that, want all For that is all to me. What is your pleasure sir? I will sir. Oh signior Angelo, No comfort but his presence can remove, This sadness from my heart. You talk iedly, If this be your best comfort keep it still, My senses cannot feed on such Sour cates. Nay leave good signior. Gods pity signior Angelo, I here my father, away for Gods sake. Pray God he meet him not. Whose there? father. At leisure? what to do? Here I am What me

**AFTER**

> Gone abroad my Lord: I but I fear heel presently return, Are you now going my most honoured Lord? No is your presence nothing, I shall want that, and wanting that, want all For that is all to me. What is your pleasure sir? I will sir. Oh signior someone, No comfort but his presence can remove, This sadness from my heart. You talk iedly, If this be your best comfort keep it still, My senses cannot feed on such Sour cates. Nay leave good signior. Gods pity signior someone, I here my father, away for Gods sake. Pray God he meet him not. Whose there? father. At leisure? what to do? Here I am What 

---

### A07495 — PURGE (1499 words)

masks: person 16, place 1, nation 2, deity 0 | tcp repairs 2, stage dirs 0 | mask_rate 0.0127

**BEFORE**

> Thy will is known, and this for answer say, 'Tis fit that wisemen should their wives obey. And now sweet duck know, I have been for my cousin Ge rardines Will and have it, a has given thee a legacy, but the to tall is Maria's. Master Doctor, your wife and master Dryfat are most well come, now were my cousin Gerardine & Master Lipsalue here, our number were complete. 'Tis here master Doctor, all his worth is Maria's and locked in a trunk, which by to morrow Sun, shall be deli uered to your custody. Cousin Gerardine, shall the Will be read before supper? It shall, read you good Master Lipsalue. 

**AFTER**

> Thy will is known, and this for answer say, 'Tis fit that wisemen should their wives obey. And now sweet duck know, I have been for my cousin Ge rardines Will and have it, a has given thee a legacy, but the to tall is someone's. Master Doctor, your wife and master someone are most well come, now were my cousin someone & Master Lipsalue here, our number were complete. 'Tis here master Doctor, all his worth is someone's and locked in a trunk, which by to morrow Sun, shall be deli uered to your custody. Cousin someone, shall the Will be read before supper? It shall, read you good Master Lipsalue.

---

### B00230 — VOTARIES (353 words)

masks: person 0, place 0, nation 0, deity 2 | tcp repairs 0, stage dirs 0 | mask_rate 0.0057

**BEFORE**

> She knew, and hath expressed it now, And so does every public vow That herd her why, and waits thy how. These, These must sure some wonders be! 1 Their very number, how it takes! 2 What harmony their presence makes! 3 How they inflame the place! Let Time then so with Love conspire, as strait be sent into the court A little Cupid, armed with fire, Attended by a jocund Sport, To breed delight, and a desire of being delighted in the nobler sort. And CUPID conquers, ever he does invade. His Victories of lightest trouble prove. For there is never labour, where is Love. Yes. All votes do in one circ

**AFTER**

> She knew, and hath expressed it now, And so does every public vow That herd her why, and waits thy how. These, These must sure some wonders be! 1 Their very number, how it takes! 2 What harmony their presence makes! 3 How they inflame the place! Let Time then so with Love conspire, as strait be sent into the court A little the god, armed with fire, Attended by a jocund Sport, To breed delight, and a desire of being delighted in the nobler sort. And the god conquers, ever he does invade. His Victories of lightest trouble prove. For there is never labour, where is Love. Yes. All votes do in one 

---

### A03189 — HERCULES (3612 words)

masks: person 79, place 32, nation 10, deity 58 | tcp repairs 0, stage dirs 0 | mask_rate 0.0496

**BEFORE**

> Have we the Cleonean Lyons torn? And decked our shoulders in their honoured spoils? The Calidoni Boar crushed with our Club? The rude Thessalian Centaurs sunk beneath Our Iuiall hand? pierced hell? bound Cerber ? And buffeted so long, till from the foam The dog belched forth strong Aconitum spring? And shall a petty river make our way To Deianeira's bed impassable? Know then the pettiest stream that flows through Greece, Il'e make thee run thy head below thy banks, Make read thy waters with thy vital blood, And spill thy waves in drops as small as tears, If thou presumest to cope with Hercules

**AFTER**

> Have we the Cleonean Lyons torn? And decked our shoulders in their honoured spoils? The Calidoni Boar crushed with our Club? The rude Thessalian the god's sunk beneath Our Iuiall hand? pierced hell? bound someone ? And buffeted so long, till from the foam The dog belched forth strong Aconitum spring? And shall a petty river make our way To Deianeira's bed impassable? Know then the pettiest stream that flows through that place, Il'e make thee run thy head below thy banks, Make read thy waters with thy vital blood, And spill thy waves in drops as small as tears, If thou presumest to cope with th

---

### A72473.3 — WAX (59 words)

masks: person 0, place 0, nation 0, deity 0 | tcp repairs 0, stage dirs 0 | mask_rate 0.0

**BEFORE**

> Aand with all fit respect. Being her Graces shadows. As he gives out, the place is, by description. I am the Chambermaid, Sir, you mistake, My Lady may see all. When he says nothing, But twirls it thus. We must obey her Graces will, and pleasure. A cruel man he is! Much ado to recover me. Or else displayed—

**AFTER**

> Aand with all fit respect. Being her Graces shadows. As he gives out, the place is, by description. I am the Chambermaid, Sir, you mistake, My Lady may see all. When he says nothing, But twirls it thus. We must obey her Graces will, and pleasure. A cruel man he is! Much ado to recover me. Or else displayed—

---

### B13574 — LANCELOT (1175 words)

masks: person 18, place 1, nation 1, deity 0 | tcp repairs 0, stage dirs 2 | mask_rate 0.017

**BEFORE**

> May it please your worship: Then to answer punctually. Then J say to'th purpose, Because your Worships vulgar understanding May meet me at the nearest: your son, my master, Or Monsieur Thomas, (for so his travel stile him) Through many foreign plots that virtue meets with, And dangers ( I beseech you give attention) Is at the last arrived To ask your (as the French man calls it sweetly) Benediction, a jour en jour. I ditt'a vou, Monsieur. Your Worship is erroneous, For as I told you, your Son Tom, or Thomas, My Master, and your son is now arrived To ask you, as our language bears it nearest Yo

**AFTER**

> May it please your worship: Then to answer punctually. Then J say to'th purpose, Because your Worships vulgar understanding May meet me at the nearest: your son, my master, Or Monsieur someone, (for so his travel stile him) Through many foreign plots that virtue meets with, And dangers ( I beseech you give attention) Is at the last arrived To ask your (as the foreign man calls it sweetly) Benediction, a jour en jour. I ditt'a vou, Monsieur. Your Worship is erroneous, For as I told you, your Son someone, or someone, My Master, and your son is now arrived To ask you, as our language bears it nea

---

### A12133 — LYSANDER (697 words)

masks: person 7, place 0, nation 0, deity 2 | tcp repairs 0, stage dirs 0 | mask_rate 0.0129

**BEFORE**

> Your graces servants. Your servant, You may command our duties, This is the Court star Philocles. All must borrow A light from him, the young Queen directs all Her favours that way. Peace, remember he is Lord Protector. He might suspect his faith, I have herd when The King who was no Epirote advanced His claim, Cassandra, our Protector now, Young then, opposed him toughly with his faction, But forced to yield had fair conditions, And was declared by the whole state next heir If the King wanted issue; our Hope's only Thrived in this daughter. Take heed, the Arras may have ears I should not weep

**AFTER**

> Your graces servants. Your servant, You may command our duties, This is the Court star someone. All must borrow A light from him, the young Queen directs all Her favours that way. Peace, remember he is Lord Protector. He might suspect his faith, I have herd when The King who was no Epirote advanced His claim, someone, our Protector now, Young then, opposed him toughly with his faction, But forced to yield had fair conditions, And was declared by the whole state next heir If the King wanted issue; our Hope's only Thrived in this daughter. Take heed, the Arras may have ears I should not weep muc

---

### A02168 — SLIPPER (1908 words)

masks: person 6, place 2, nation 4, deity 0 | tcp repairs 9, stage dirs 0 | mask_rate 0.0063

**BEFORE**

> Why I must talk on Idy fort, wherefore was my tongue made. Come under mine arm sir, or get a footstool, Or else by the light of the Moon, I must come to it. And I can lick a dish before a Cat. How mean you that sir, of what trade? Marry I'll tell you, I have many trades, The honest trade when I needs must, The filching trade when time serves, The Cosening trade as I find occasion. And I have more qualities, I cannot abide a full cup unkissed, A fat Capon vncaru'd, A full purse unpicked, Nor a fool to prove a Justice as you do. This is my little brother with the great wit, beware him, But what 

**AFTER**

> Why I must talk on someone fort, wherefore was my tongue made. Come under mine arm sir, or get a footstool, Or else by the light of the Moon, I must come to it. And I can lick a dish before a Cat. How mean you that sir, of what trade? Marry I'll tell you, I have many trades, The honest trade when I needs must, The filching trade when time serves, The Cosening trade as I find occasion. And I have more qualities, I cannot abide a full cup unkissed, A fat Capon vncaru'd, A full purse unpicked, Nor a fool to prove a Justice as you do. This is my little brother with the great wit, beware him, But w

---

### A07493 — WELSH GENTLEWOMAN (135 words)

masks: person 0, place 1, nation 3, deity 0 | tcp repairs 0, stage dirs 0 | mask_rate 0.0296

**BEFORE**

> Dugat a whee. I can Sir simply. I know not what he means, A Suitor quoth a? I hold my life he understands no English. What's this fertur and abundundis? He mocks me sure, and calls me a bundle of Farts. This is most strange, may be he can speak Welch, Auedera whee comrage, der endue cog foginis. Rhegosin a whiggin harle ron corid ambre. As well as ever we did before we met. You put me to a Man I understand not, Your Son's no English Man me thinks. I have been long enough in the chamber with him, And I find neither Welch nor English in him. It's quickly pardoned forsooth. Nay good sweet Time. S

**AFTER**

> Dugat a whee. I can Sir simply. I know not what he means, A Suitor quoth a? I hold my life he understands no foreign. What's this fertur and abundundis? He mocks me sure, and calls me a bundle of Farts. This is most strange, may be he can speak Welch, Auedera whee comrage, der endue cog foginis. That place a whiggin harle ron corid ambre. As well as ever we did before we met. You put me to a Man I understand not, Your Son's no foreign Man me thinks. I have been long enough in the chamber with him, And I find neither Welch nor foreign in him. It's quickly pardoned forsooth. Nay good sweet Time.

---

### A02127 — JOAN (64 words)

masks: person 3, place 0, nation 0, deity 0 | tcp repairs 0, stage dirs 0 | mask_rate 0.0469

**BEFORE**

> Margret a farmers daughter for a farmers Son , I warrant you the meanest of us both, Shall have a mate to lead us from the Church: But Thomas whats the news? what in a dump. Give me your hand, we are near a pedlars shop, Out with your purse we must have fairings now. What Margret blush not, maids must have their loves.

**AFTER**

> Someone a farmers daughter for a farmers Son , I warrant you the meanest of us both, Shall have a mate to lead us from the Church: But someone whats the news? what in a dump. Give me your hand, we are near a pedlars shop, Out with your purse we must have fairings now. What someone blush not, maids must have their loves.

---

### A68727 — GRATIANO (1100 words)

masks: person 23, place 2, nation 0, deity 0 | tcp repairs 0, stage dirs 0 | mask_rate 0.0227

**BEFORE**

> Well keep me company but two years more Thou shalt not know the found of thine own tongue. Thanks i'faith, for silence is only commendable In a neats togue dried, and a maid not vendable. I have suit to you. You must not deny me, I must go with you to Belmont. Signor Bassanio, hear me, If I do not put on a sober habit, Talk with respect, and swear but now and than, Wear prayer books in my pocket, look demurely, Nay more, while grace is saying hood mine eyes Thus with my hat, and sighs and say amen: Use all the observance of civility Like one well studied in a sad ostent To please his Grandam, 

**AFTER**

> Well keep me company but two years more Thou shalt not know the found of thine own tongue. Thanks i'faith, for silence is only commendable In a neats togue dried, and a maid not vendable. I have suit to you. You must not deny me, I must go with you to Belmont. Signor someone, hear me, If I do not put on a sober habit, Talk with respect, and swear but now and than, Wear prayer books in my pocket, look demurely, Nay more, while grace is saying hood mine eyes Thus with my hat, and sighs and say amen: Use all the observance of civility Like one well studied in a sad ostent To please his Grandam, n

---

### A04658 — PINNACIA (455 words)

masks: person 2, place 0, nation 1, deity 0 | tcp repairs 0, stage dirs 0 | mask_rate 0.0066

**BEFORE**

> He is a foolish fellow, I pray you mind him not, He is my Protection. You ee what your entreaty, and pressure still Of gentlemen, to be civil, does bring on? A quarrel? and perhaps manslaughter? You Will carry your goose about you, still? your plam king Your tongue to smooth all is not here fine stuff? Your wife? ha'not I for iden you that Do you think I'll call you husband this gown, Or any thing, in that jacket, but Protection? Here tie my shoe; and show my vellute petticoat, And my silk stocking! why do you make me a Lady, If I may not do Like a Lady, in fine clothes. ; I knew that at home;

**AFTER**

> He is a foolish fellow, I pray you mind him not, He is my Protection. You ee what your entreaty, and pressure still Of gentlemen, to be civil, does bring on? A quarrel? and perhaps manslaughter? You Will carry your goose about you, still? your plam king Your tongue to smooth all is not here fine stuff? Your wife? ha'not I for iden you that Do you think I'll call you husband this gown, Or any thing, in that jacket, but Protection? Here tie my shoe; and show my vellute petticoat, And my silk stocking! why do you make me a Lady, If I may not do Like a Lady, in fine clothes. ; I knew that at home;

---

### A11152 — HULDRICK (185 words)

masks: person 5, place 3, nation 0, deity 0 | tcp repairs 0, stage dirs 1 | mask_rate 0.0432

**BEFORE**

> Dioclesian, hear me. Proud Roman this: if here thou longer stay, He'll peck thine Eagles eyes out, make thee a prey To his stern Gripe, whose dismal beak now sings the sudden ruin If thou deny it, By the glorious Sun, and all the Deities our men adore, We'll forage up to Room and Italy, and fit In triumph in your Capitol: the Vandals and the Goaths shall carve Their fame's as deep as now the Roman do their Names: Raise up as many Trophies, and as high, In brazen pillars of their victory. Spirits infernal could not charge so hotly; Disgraced i'th' onset: counsel Roderick, what's to be done? Our

**AFTER**

> Dioclesian, hear me. Proud someone this: if here thou longer stay, He'll peck thine Eagles eyes out, make thee a prey To his stern Gripe, whose dismal beak now sings the sudden ruin If thou deny it, By the glorious Sun, and all the Deities our men adore, We'll forage up to Room and that place, and fit In triumph in your that place: the Vandals and the that place shall carve Their fame's as deep as now the someone do their Names: Raise up as many Trophies, and as high, In brazen pillars of their victory. Spirits infernal could not charge so hotly; Disgraced i'th' onset: counsel someone, what's 

---

### A12969 — COCK (397 words)

masks: person 5, place 0, nation 0, deity 0 | tcp repairs 0, stage dirs 0 | mask_rate 0.0126

**BEFORE**

> ¶ How Gammer. ¶ That shall be done anon. ¶ Ich cannot get the Candle light here is almost no fire. ¶ Gogs cross Gammer if you will laugh look in but at the door And see how Hodg lies tumbling and tossing amids the flour Raking there some fair to find among the ashes dead Where there is not one spark, so big as a pins head, At last in a dark corner two sparks he thought he sees Which where indeed no ght else but Gyb our cats two eyes Puff quod hodg thinking thereby to have fire without doubt With that Gyb shut her two eyes, & so the fire was out And by and by them opened, even as they were befo

**AFTER**

> How Gammer. That shall be done anon. Ich cannot get the Candle light here is almost no fire. Gogs cross Gammer if you will laugh look in but at the door And see how Hodg lies tumbling and tossing amids the flour Raking there some fair to find among the ashes dead Where there is not one spark, so big as a pins head, At last in a dark corner two sparks he thought he sees Which where indeed no ght else but Gyb our cats two eyes Puff quod hodg thinking thereby to have fire without doubt With that Gyb shut her two eyes, & so the fire was out And by and by them opened, even as they were before, With

---

### A05206 — CORDELLA (1693 words)

masks: person 9, place 0, nation 0, deity 0 | tcp repairs 1, stage dirs 0 | mask_rate 0.0053

**BEFORE**

> Oh, how I do abhor this flattery! I cannot paint my duty forth in words, I hope my deeds shall make report for me: But look what love the child does owe the father, The same to you I bear, my gracious Lord. The praise were great, spoke from another's mouth: But it should seem your neighbours dwell far off. What then is left for his third daughters dowry, Lovely Cordella, whom the world admires? Ah Pilgrim's, what avails to show the cause, When there's no means to find a remedy? To touch a soar, does aggravate the pain. Kind Palmer, which so much defir'st to hear The tragic tale of my unhappy y

**AFTER**

> Oh, how I do abhor this flattery! I cannot paint my duty forth in words, I hope my deeds shall make report for me: But look what love the child does owe the father, The same to you I bear, my gracious Lord. The praise were great, spoke from another's mouth: But it should seem your neighbours dwell far off. What then is left for his third daughters dowry, Lovely someone, whom the world admires? Ah Pilgrim's, what avails to show the cause, When there's no means to find a remedy? To touch a soar, does aggravate the pain. Kind Palmer, which so much defir'st to hear The tragic tale of my unhappy yo

---

### A20951 — MICHAEL (1598 words)

masks: person 25, place 1, nation 0, deity 0 | tcp repairs 1, stage dirs 3 | mask_rate 0.0163

**BEFORE**

> To fetch my Master's nag, I hope yowl think on me. But he hath sent a dagger sticking in a heart, With a verse or two stolen from a painted cloth: The which I here the wench keeps in her chest, Well let her keep it, I shall find a fellow That can both write and read, and make rhyme too, And if I do, well, I say no more: I'll send from London such a taunting letter, As shall eat the heart he sent with salt, And sling the dagger at the Painters head. I'll see he shall not live above a week. I understand the Painter here hard by, Hath made report that he and Sue is sure. Why then I say that I wil

**AFTER**

> To fetch my Master's nag, I hope yowl think on me. But he hath sent a dagger sticking in a heart, With a verse or two stolen from a painted cloth: The which I here the wench keeps in her chest, Well let her keep it, I shall find a fellow That can both write and read, and make rhyme too, And if I do, well, I say no more: I'll send from that place such a taunting letter, As shall eat the heart he sent with salt, And sling the dagger at the Painters head. I'll see he shall not live above a week. I understand the Painter here hard by, Hath made report that he and Sue is sure. Why then I say that I

---

### A04633.1 — PURECRAFT (866 words)

masks: person 8, place 0, nation 0, deity 0 | tcp repairs 0, stage dirs 0 | mask_rate 0.0092

**BEFORE**

> Look up, sweet Win-the-fight, and suffer not the enemy to enter you at this door, remember that your education has been with the purest, what polluted one was it, that named first the un clean beast, Pig, to you, Child? Oh! resist it, Win-the-fight, it is the Tempter, the wicked Tempter, you may know it by the fleshly motion of Big, be strong against it, and it's foul temptations, in these assaults, whereby it broacheth flesh and blood, as it were, on the weaker side, and pray against it's carnal provocations, good child, sweet child, pray. What shall we do? call our zealous brother Busy hithe

**AFTER**

> Look up, sweet someone-the-fight, and suffer not the enemy to enter you at this door, remember that your education has been with the purest, what polluted one was it, that named first the un clean beast, Pig, to you, Child? Oh! resist it, someone-the-fight, it is the Tempter, the wicked Tempter, you may know it by the fleshly motion of Big, be strong against it, and it's foul temptations, in these assaults, whereby it broacheth flesh and blood, as it were, on the weaker side, and pray against it's carnal provocations, good child, sweet child, pray. What shall we do? call our zealous brother so

---

### A11911 — CHORUS (6033 words)

masks: person 101, place 41, nation 31, deity 29 | tcp repairs 115, stage dirs 0 | mask_rate 0.0335

**BEFORE**

> Anapaestici et ultimus Jambicus. I Am rara micant sidera prono Languida mundo, nox victa, vagos Contrahit ignes, luce renata. Cogit nitidum Phosphoros agmen. Signum celsi glacial poli, Septem stellis Arcades ursae, Lucem verso temone vocant. Jam caeruleis evectus equis Titan, summum prospicit Oethan. Jam Cadmaeis inclyta baccis Aspersa die dumeta rubeur, Phoebi que fugit reditura soror. Labour exoritur durus, & omneis Agitat curas, aperit que domos Pastor, gelida canam pruina Grege dimisso pabula carpit. Ludit prato liber aperto, Nond im rupta front ivuencus. Vacuae reperant ubera matres. Erra

**AFTER**

> Anapaestici et ultimus that place. I Am rara micant sidera prono Languida mundo, nox victa, vagos foreign ignes, luce renata. Cogit nitidum that place agmen. Signum celsi glacial poli, Septem stellis Arcades ursae, someone verso temone vocant. Jam caeruleis evectus equis the god, summum prospicit someone. Someone inclyta baccis Aspersa die dumeta rubeur, someone que fugit reditura soror. Labour exoritur durus, & omneis Agitat curas, aperit que domos Pastor, gelida canam pruina Grege dimisso pabula carpit. Ludit prato liber aperto, that place im rupta front ivuencus. Someone reperant ubera matr

---

### A02738 — INFIDELITY (4187 words)

masks: person 37, place 2, nation 6, deity 2 | tcp repairs 56, stage dirs 1 | mask_rate 0.0112

**BEFORE**

> ♫ Broom, broom, broom, broom, broom. Buy broom buy ♫ buy. Bromes for shoes and pow h Rings, boats and ♫ buskyns for new bromes / Broom, broom, broom. Marry God give you good even, And the holy man Saint Steven, Send you a good new year. I would have brought you the pax. Or else anymage of wax. If I had known you hear. I will my self so handle. That you shall have a candle, When I come hither again. At this your Sudden motion. I was in soch devotion, I had never broke a vain. No, no, it was but a fart, For pastime of my heart, I would you had it forsooth. In serupp or in souse, But for noyance 

**AFTER**

> ♫ Broom, broom, broom, broom, broom. Buy broom buy ♫ buy. Bromes for shoes and pow h Rings, boats and ♫ buskyns for new bromes / Broom, broom, broom. Marry God give you good even, And the holy man someone, Send you a good new year. I would have brought you the pax. Or else anymage of wax. If I had known you hear. I will my self so handle. That you shall have a candle, When I come hither again. At this your Sudden motion. I was in soch devotion, I had never broke a vain. No, no, it was but a fart, For pastime of my heart, I would you had it forsooth. In serupp or in souse, But for noyance of th

---

### A09214 — PEDANTIUS (7600 words)

masks: person 151, place 49, nation 18, deity 15 | tcp repairs 46, stage dirs 0 | mask_rate 0.0307

**BEFORE**

> Dromodote, Sis bonus o foelix que tuis, sicut sapiens dixit poêta. Ut vam lent sodalis nostri Academici? numquid adhuc convenit inter vos & oppidanos? Cogitabam iàm dudum ipse vos invise re, & quosdam in Scholis Rhetoricis recitare Declamationes meas, quae nempe, ut Demostheni, lucernam oh lent. Composuj, congessi, consarci nauj tres plusquam Philippicas, aut Catilinarias contra barbaram gentem quid dixi? gentem? certè vero potiùs armentum Oppidanorum istorum hosti um Musarum; qui tamen vivunt, imo in forum veniunt, idque non and depo nendam, said confirmandam audaciam. Fama, malum ̄ quo non a

**AFTER**

> Dromodote, Sis bonus o foelix que tuis, sicut sapiens dixit poêta. Ut vam lent sodalis nostri someone? numquid adhuc convenit inter vos & oppidanos? Cogitabam iàm dudum ipse vos invise re, & quosdam in that place recitare foreigners meas, quae nempe, ut someone, lucernam oh lent. Composuj, congessi, consarci nauj tres plusquam that place, aut Catilinarias contra barbaram gentem quid dixi? gentem? certè vero potiùs armentum Oppidanorum istorum hosti um Musarum; qui tamen vivunt, imo in forum veniunt, idque non and depo nendam, said confirmandam audaciam. Fama, malumm quo non aliud velo cius ull

---

### A04052 — REMEDY (1755 words)

masks: person 0, place 0, nation 3, deity 0 | tcp repairs 41, stage dirs 0 | mask_rate 0.0017

**BEFORE**

> I am be that ought for to be well known Of you three specially, and of duty Great pain and business as for mine own For you I have taken because I lo e you heartily To m I taine you is all my de ire and faculty yet hard it is to do, the people be so variable And many be so wilful, they will not be reformable. I pardon you, for I do know you w l both well h, and l h, is your That which ngla worser to forbe e were very lot For by wealth and health comes re all sa es Many other e nes or our gre to wealth ames TO a they a e not pre ume, nor thy dare no e bold All that I do intend, if you will ther

**AFTER**

> I am be that ought for to be well known Of you three specially, and of duty Great pain and business as for mine own For you I have taken because I lo e you heartily To m I taine you is all my de ire and faculty yet hard it is to do, the people be so variable And many be so wilful, they will not be reformable. I pardon you, for I do know you w l both well h, and l h, is your That which ngla worser to forbe e were very lot For by wealth and health comes re all sa es Many other e nes or our gre to wealth ames TO a they a e not pre ume, nor thy dare no e bold All that I do intend, if you will ther

---

### A02738 — LAW OF CHRIST (1854 words)

masks: person 10, place 4, nation 1, deity 1 | tcp repairs 39, stage dirs 0 | mask_rate 0.0086

**BEFORE**

> If thu heardest of me, it was by the voice of God. If he spoke of me, he was some godly preacher, After what manner, dead he speak of me? tell. That speaking is soch, as procureth eternal pain. Will not the people, leave that most wicked folly? And is so damnable? To hear it I am sorry. But what dedyst thu mean, wha ̄ thu spokest of my wife? Why, how good am I? thy fantasy declare. As thu art, thu speakest, after they hearts abundau ̄ ce For as the man is, soch in his utterance. My wife is the church, or Christian congregation, Regenerate in sprete, doing no vile operation, Both clean and holy

**AFTER**

> If thu heardest of me, it was by the voice of God. If he spoke of me, he was some godly preacher, After what manner, dead he speak of me? tell. That speaking is soch, as procureth eternal pain. Will not the people, leave that most wicked folly? And is so damnable? To hear it I am sorry. But what dedyst thu mean, wham thu spokest of my wife? Why, how good am I? thy fantasy declare. As thu art, thu speakest, after they hearts abundaum ce For as the man is, soch in his utterance. My wife is the church, or someone congregation, Regenerate in sprete, doing no vile operation, Both clean and holy, wi

---

### A04632.3 — CHORUS (44 words)

masks: person 0, place 0, nation 0, deity 11 | tcp repairs 0, stage dirs 0 | mask_rate 0.25

**BEFORE**

> Good MERCURY defend us. Good MERCURY defend us. Good MERCURY defend us. Good MERCURY defend us. Good MERCURY defend us. Good MERCURY defend us. Good MERCURY defend us. Good MERCURY defend us. Good MERCURY defend us. Good MERCURY defend us. Good MERCURY defend us.

**AFTER**

> Good the god defend us. Good the god defend us. Good the god defend us. Good the god defend us. Good the god defend us. Good the god defend us. Good the god defend us. Good the god defend us. Good the god defend us. Good the god defend us. Good the god defend us.

---

### A06184 — LICTORS (38 words)

masks: person 4, place 1, nation 0, deity 2 | tcp repairs 0, stage dirs 0 | mask_rate 0.1842

**BEFORE**

> The pour of Scylla nought will veil gainst Room, And let me die Lucretius ere I see, Our Senate dread for any private man, Therefore Renowned Sulpitius send for Scylla back, Let Marius lead our men in Asia.

**AFTER**

> The pour of the god nought will veil gainst Room, And let me die someone ere I see, Our Senate dread for any private man, someone send for the god back, Let someone lead our men in that place.

---

### A11954.26 — HERALD (40 words)

masks: person 7, place 0, nation 0, deity 0 | tcp repairs 0, stage dirs 0 | mask_rate 0.175

**BEFORE**

> Know Room, that all alone Martius did fight Within Corioles Gates: where he hath won, With Fame, a Name to Martius Caius: These in honour follows Martius Caius Coriolanus. Welcome to Room, renowned Coriolanus. Give way there, and go on.

**AFTER**

> Know Room, that all alone someone did fight Within Corioles Gates: where he hath won, With Fame, a Name to someone: These in honour follows someone. Welcome to Room, renowned someone. Give way there, and go on.

---

### A06184 — GENIUS (46 words)

masks: person 4, place 4, nation 0, deity 0 | tcp repairs 0, stage dirs 0 | mask_rate 0.1739

**BEFORE**

> Subsequitur tua ors: privari lumine Scillam, Numina Parcarum am feram precipiunt. Precipiunt feram jam Parcarum numina, Scillam, Lumine privari, mors tua subsequitur, Elysium petis, o foelix! & fatidici astri: Praescius Heroas, o petis innumeros! Innumeros petis o Heroas! praescius astri Fatidici: & foelix, o petis Elisium!

**AFTER**

> Subsequitur tua ors: privari lumine that place, someone am feram precipiunt. Precipiunt feram jam that place numina, someone privari, mors tua subsequitur, that place petis, o foelix! & fatidici astri: someone, o petis innumeros! Innumeros petis o that place! praescius astri Fatidici: & foelix, o petis Elisium!

---

### A11954.20 — 2 MESSENGER (52 words)

masks: person 3, place 5, nation 1, deity 0 | tcp repairs 0, stage dirs 0 | mask_rate 0.1731

**BEFORE**

> Thou Princely Leader of our English strength, Never so needful on the earth of France, Spur to the rescue of the Noble Talbot, Who now is girdled with a waste of Iron, And hemmed about with grim destruction: To Bordeaux warlike Duke, to Bordeaux York, Else farewell Talbot, France, and England's honour.

**AFTER**

> Thou Princely Leader of our foreign strength, Never so needful on the earth of that place, Spur to the rescue of the Noble someone, Who now is girdled with a waste of Iron, And hemmed about with grim destruction: To that place warlike Duke, to that place someone, Else farewell someone, that place, and that place's honour.

---

