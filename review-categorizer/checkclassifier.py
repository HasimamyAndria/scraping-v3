from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline


def checkclassifier(categories, text):
    try:
        prediction = {'séquence': text, 'labels': [], 'scores': []}
        # classifier = pipeline(task="zero-shot-classification",
        #                       device=-1, model="facebook/bart-large-mnli")
        classifier = pipeline("zero-shot-classification",
                              device=-1, model="cross-encoder/nli-deberta-v3-base")

        # categs = list(map(lambda x: x['category'], categories))
        categs = categories

        prediction = classifier(text, categs, multi_label=True)

        # for categ in categs:
        #     result = classifier(text, categ, multi_label=False)

        #     # print(result)
        #     prediction['labels'].append(categ)
        #     prediction['scores'].append(result['scores'][0])

        # prediction = classifier(
        # text, list(map(lambda x: x['category'], categories)), multi_label=False)
        # text, categories, multi_label=True)

        print('\n', prediction)

    except Exception as e:
        print(e)
        pass


categs = ['Furniture', 'Home', 'Housekeeping', 'Location', 'Food', 'Driving']
texts = [
    'Had a great meal with friends celebrating a birthday. Food, service was all excellent, would definitely visit again.',
    'Lamb was not nice but place is friendly and nice vibe',
    'Very nice staff. Setting good . Food not fantastic but very acceptable',
    'Absolutely wonderful wines and food. We enjoyed it very much.',
    'Great Christmas Day lunch, made memorable by the lovely service from all but one of the staff.',
    'Very nice lunch with friends. Staff were friendly and patient. Food was good and I would certainly recommend.',
    'The food here is consistently good: no nonsense modern European brasserie food. A good wine list. We did feel a little rushed for a 6.30 sitting. I love it here.',
    'Attended 28-50 for a work lunch. Would highly recommend the food was amazing as were the staff.',
    'Food very good but main course came out before starter cleared. Prawns delicious as was lamb shoulder. Most wines ridiculously expensive with none under £50. Most over €£100 Service pleasant and friendly',
    'Most of the food choices we made were very good . However, we were’t impressed with the flavour or value of the prawns (starter) . The staff were extremely good, hot, as was the ambience.',
    'Lovely food but odd service. The main course came out late for which the waiter apologised. The next thing we knew was that the kitchen was closed and we couldn\'t have a dessert.... We felt that perhaps the waiter could have taken our dessert order before the kitchen closed!!!! But the scotch egg starter is great!!! Worth the trip.',
    'Despite booking and reservation was on the system, there was no table available as the restaurant was overbooked. We were offered by the bar or by the door were there was a constant flow of cold air. Food was casual dining fairly average and overall average for the price. There are much better places to go in the area.',
    'Good food, service and ambiance. Nice wine selection too!',
    'We weren\'t impressed. Arrived to be told the resto needed the table back after 2 hours, something we were not told about when booking. Very slow service from what felt like an experienced wait staff. Were not told that we needed to order separate sides, so when we did there was another delay. Pretty amateur.',
    'Delicious food and wine (and great range of wines by the glass).',
    'Lovely meal and super service. On the day I met a friend for lunch at 28-50, Madeline was managing the restaurant. What a charming young lady, with exemplary hospitality skills. All the staffl came up to the mark, and we two \'old ladies" had an extremely good experience. I would return at the drop of a hat!',
    'The success of our lunch was made by the polite & attentive staff.',
    'The perfect venue to meet up with friends pre Christmas. Service always impeccable, food quality consistently excellent and wine choice really good.',
    'We could not enjoy our dinner , because when we arrived even if I booked a standard table they gave us a top table and no other option,l. We asked for a normal one as I booked that but they do not even tried , they said they are fully booked. Very disappointed and un professional',
    'Dangerous and illegal driving',
    'MV Transfers - Great customer service: I can\'t recommend MV transfers highly enough. We had to amend our booking at very late notice and MV Transfers allowed us to do this despite having no obligation to help. Our transfer drivers were on time and helpful. We will definitely use MV Transfers again.',
    'Very happy with the service: Very happy with the service. Drivers were at the airport waiting to collect us on our arrival and also early in the morning to take us from the hotel for our departure. Drivers were friendly and help. Have used MV transport before and will use them again.',
    'First class service: We used this company for the first time this year, and found them to be first class,the transfer arrived on time, the driver was helpful and friendly, after our experience we will now he using them every time.',
    'Great transfer company: Have just had a fabulous week in Flaine. We had trouble getting a reasonably pieced transfer from Geneva. Ended up finding MVtransport buried in an internet. They were excellent, well priced, on time and communicated well including changing pick up time to allow us more time to navigate Geneva airport. Can’t recommend them enough.',
    'Can’t fault them!!: Found MV Transport to be one of the cheapest quotes, fraction of the price I was going to pay another company for multi drop transfer, MV could do a private one! Extremely efficient, waiting for us outside arrivals and smooth journey to our destination in the mountains. Then again on our return transfer, on time and another smooth journey!'
]

for t in texts:
    checkclassifier(categs, t)
