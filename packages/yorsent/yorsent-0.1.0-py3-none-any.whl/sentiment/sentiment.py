import string
from pathlib import Path
import re
from collections import Counter
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
import pickle
import pandas as pd

# Yoruba Stopwords List
yoruba_stopwords = set([
    "ni", "ati", "sí", "lori", "gbogbo", "sugbon", "pẹlu", "fún", "nitori", "mo", "a",
    "o", "ó", "wọ́n", "mò", "à", "ò", "ẹ̀", "n", "wọn", "kò", "kọ́", "mi", "wa", "yín", "i", "ẹ́", "é", "á", "ú",
    "u", "ọ́", "ọ", "í", "kì", "kìí", "ín", "in", "án", "an", "un", "ún", "ọ́n", "ọn", "tàbí", "ṣùgbọ́n", "wọ̀nyí", "wọ̀nyẹn", "èyí", "ìyẹn",
    "ní", "tí", "ti", "bí", "tilẹ̀", "jẹ́pé", "nígbà", "nígbàtí", "yóò", "máa", "màá", "ń", "náà", "yìí", "kí", "yẹn", "si"
])

# Positive, Negative, and Neutral Words Lists
positive_words = ["ayọ̀", "ire", "ìbùkún", "àlàáfíà", "gbèjà", "ìdùnnú", "ìlera", "oríire", "dáadáa", "dada",
                  "ìgbádùn", "àjọyọ̀", "àjọ̀dún", "òmìnira", "ìtẹ̀síwájú", "ìrọ̀rùn", "àǹfààní", "làmìlaaka", "ìlọsíwájú",
                  "ìmọrírì", "àṣeyọrí", "ròkè", "pẹ́ẹ́lí", "pèsè", "ìrètí", "Ayọ̀", "Ire", "Adùn", "Ajé", "Ìmọ́lẹ̀", "Ọrọ̀", "Sùúrù", "Ọ̀rẹ́", "Akínkanjú", "Àṣeyọrí",
                  "Òtítọ́", "Ìrẹ̀lẹ̀", "Ìlera", "Itẹríba", "Ìtẹ́lọ́rùn", "Ìdẹ̀ra", "Fẹ́ràn", "Eré", "Àlìkámà",
                  "Tutù", "Ayọ̀", "Àlàáfíà", "Ìbùkún", "Ìfẹ́", "Àṣeyọrí", "Ìyìn", "Ìlera", "Ìdùnú", "Ọlá",
                  "Iṣégun", "Àánú", "Ọ̀rẹ́", "Ìkànsí", "Ìtẹ́lọ́run", "Àtọ́kànwá", "Ẹ̀bùn", "Ìmọ̀lára rere", "Ìtura",
                  "Ìdárayá", "Ìfaradà", "Ayo", "Nifẹ", "Ire", "Àlàáfíà", "Àṣeyọrí", "Ola", "Ireti", "Ìdùnnú",
                  "Ṣíṣe", "Itelorun", "Ibunkun", "Dára", "Yanilenu", "Laṣiri", "Ìgboyà", "Òtítọ", "Ṣé", "Orire",
                  "Ronú", "Gbọn", "Àlàáfíà", "Ayọ̀", "Ìrètí", "Ìfẹ́", "Àṣeyọrí", "Ìfọkànsí", "Òtítọ́", "Ìgbèkẹ̀lé",
                  "Aláàánú", "Oríire", "Ìwà rere", "Ìlera", "Ìbùkún", "Ìgboyà", "Ọpẹ", "Ìṣẹ́gun", "Ìdùnnú",
                  "ìlósìwájú", "Ìpẹ́lẹ́", "Ìmísí", "Ìdùnnú", "Ìfẹ́", "Àlàáfíà", "Ìrètí", "Ìgboyà", "Àṣeyọrí",
                  "Ìlera", "Oore", "Ọ̀rẹ́", "Ìrànlọ́wọ́", "Ìmọ̀", "Ìgbàgbọ́", "Ìtẹ́lọ́rùn", "Ìwà rere", "Ìyìn",
                  "Ìgbórí", "Ìrísí", "Ìfọ̀rọ̀wọ́pọ̀", "Ìtùnú", "Ìṣọ̀rẹ́", "Ayò/ìdùnú", "Èrín", "Àlàáfía", "Orò",
                  "Ïfé", "Àseyorí", "Ìtélórùn", "Ìbùkún", "Ìgbàgbó", "Ìrépò", "Ôòtó", "Ologbón", "Ìfokàbalè",
                  "Rere/dídára", "Ìlera", "Òtímí", "Ìgboyà", "Ìmólè", "Tutù", "Wùrà", "Rere", "Ayò", "Ìyè",
                  "Rere", "Ìtura", "Èrín", "Ìlera", "Ìmólè", "Òré", "Orò", "Olórò", "Sàn", "Adún", "Ìgbádùn",
                  "Òpò", "Ní", "Rewá", "Omo", "Gbón", "Àdúrà"
]
negative_words = ["ibi", "kú", "ìpọ́njú", "àìbàlẹ̀-ọkàn", "ogun", "ìbànújẹ́", "ikú", "àìní", "àìsàn", "àìlera",
                  "ọ̀fọ̀", "òfò", "ìfòòró", "burú", "burúkú", "rògbòdìyàn", "wàhálà", "ìdààmú", "ìwọ́de", "ìfẹ̀hónúhàn",
                  "ìfàsẹ́yìn", "àìbìkítà", "ẹkún", "ọ̀wọ́ngógó", "ìpèníjà", "èèṣì", "àìrajaja", "léèmọ̀", "ìjìyà", "ẹ̀wọ̀n", "ìṣekúpa",
                  "Ìbànújẹ́", "Ibi", "Ìkorò", "Òkùtà", "Òkùnkùn", "Òsì", "Ìbínú", "Ọ̀tá", "Ọ̀lẹ", "Àṣetì",
                  "Irọ́", "Ìgbéraga", "Àìsàn", "Àrínfín", "Ojúkòkòrò", "Ìnira", "Kórira", "Ìjà", "Èpò", "Gbóná",
                  "Ìbànújẹ́", "Ìbínú", "Ìfarapa", "Ìkà", "Ọ̀tẹ̀", "Ìbànilẹ́nu", "Ìtànjẹ", "Ìfarapa ọkàn", "Iro",
                  "Òtẹ̀lú", "Ofo", "Ekun", "Ẹ̀sùn", "Èṣù", "Òjòburúkú", "Ikorira", "Ìrètíkúrò", "Ìtẹ̀míjù", "Ìkọlà",
                  "Ìfẹ̀kúfẹ̀", "Ìbànújẹ", "Ainife", "Aburu", "AiÀlàáfíà", "Aialaseyori", "Sulola", "Ainireti",
                  "Edun ọkan", "Aisise", "Ainitelorun", "Ainibunkun", "Aidara", "Aiyanilenu", "Ailasisri", "Ainigboya",
                  "Ailotito", "Aisẹ", "Oriibu", "Sotobi", "Aigbon", "bú", "kú", "rírùn", "ìjà", "òfò", "èbi", "àìsàn",
                  "ìkà", "ewú", "dòdò", "òyì", "gbígbóná", "àánú", "ìpòkú", "òṣì", "rò", "òkùnkùn", "dìgbòlugi",
                  "gbígbẹ", "wúwo", "Ìbànújẹ́", "Ìbẹ̀rù", "Ìbínú", "Ìtìjú", "Ìkórìíra", "Ìpọ́njú", "Ìṣòro",
                  "Ìpalára", "Ìfẹ̀gàn", "Ìwà ipá", "Ìparun", "Ìfẹ̀sùnmọ́ni", "Ìṣubú", "Ìkùnà", "Ìbúgbé", "Ìdààmú",
                  "Ìṣekúṣe", "Ìwà àgàgà", "Ìwà ọ̀dà", "Ìfẹ́kúfẹ̀", "Ìbànújé", "Ekú", "Àilera", "Ìsé", "Ìkórira",
                  "Ìkùnà", "Ìfèkúfè", "Ègún", "Iyèméjì", "Ìyapa", "Ètàn", "Òmùgò", "Ìdàmú", "Búburú", "Àisàn",
                  "Èké", "Ìbèrù", "Òkùnkùn", "Gbóná", "Ide", "Ibi", "Ìbànújé", "Ikú", "Búburú", "Ìnira", "Ekún",
                  "Àisàn", "Òkùnkùn", "Òtá", "Òsì", "Tálákà", "Le", "Ìkorò", "Ìyà", "Àiní", "Bùrewà", "Erú",
                  "Gò", "Èpé", "Ìbànújẹ", "Ìbínú", "Ìkà", "Ẹ̀gàn", "Ìfarapa", "Àníyàn", "Ìjà", "Ìṣekúṣe", "Ẹ̀tàn",
                  "Àṣìṣe", "Ìpẹyà", "Ìtẹ́gùn", "Ìṣòro", "Àbùkù", "Ọràn", "Ìfarapa ọpọlọ", "Ìjìyà", "Ẹ̀jọ́",
                  "Ìdènà", "Ìkúnlẹ̀ abẹ́là", "Alaigbonran", "Ibinu", "Ipa", "Ipalara", "Esu", "Esun", "Asise",
                  "Ofo", "Agan", "Aini", "Ise", "Aisan", "Iberu", "Ibanuje", "Inira", "Ika", "Ojukokoro",
                  "Eke", "Ote", "Iya", "Aburú", "Ìkórira", "Wàhálà", "Ìdèra", "Owú", "Ìbínú", "Ìjayà", "Ìsòro",
                  "Ìkùnà", "Èsan", "Àìmòkan", "Ìlara", "Màjèlé", "Ìpónjú", "Èèwò", "Èpè", "Ètàn", "Èsù",
                  "Ìgbéraga", "Àníyàn", "Ibanuje", "Irora", "Itiju", "Iberu", "Idaamu", "Egan", "Ija", "Kabamo",
                  "Ibinu", "Ika", "ifarapa", "Aiseyori", "Abuku", "Ailera", "Ote", "Ifekufe", "Ikorira", "Aibowo",
                  "Buburu", "Okunkun"
]
neutral_words = ["wa", "ni", "orukọ", "ṣe", "wọn", "pe", "a", "ti", "lati", "si", "gẹgẹ", "bi", "bá", "lati", "de", "le", "wá",
                 "yi", "yìí", "náà", "lẹ́yìn", "kan", "tí", "o", "a", "kì", "nkan", "lọ", "fi", "ṣe", "kó", "tó", "wọlé"]

def preprocess_text(text):
    """ Converts text to lowercase, removes punctuation, tokenizes words, and filters out Yoruba stopwords. """
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    tokens = text.split(' ')
    filtered_tokens = [word for word in tokens if word not in yoruba_stopwords]
    return ' '.join(filtered_tokens)

def most_frequent_words(tokens, n=10):
    """ Computes and returns the top N most frequent words using NLTK and Counter. """
    word_freq = Counter(tokens)
    return word_freq.most_common(n)

def hybrid_predict(text):
    """
    Combines the machine learning model prediction with a keyword-based override.
    """
    processed_text = preprocess_text(text)
    text_vec = vectorizer.transform([processed_text])
    model_prediction = sentiment_model.predict(text_vec)[0]

    tokens = processed_text.split()
    pos_count = sum(1 for word in tokens if word in positive_words)
    neg_count = sum(1 for word in tokens if word in negative_words)

    if pos_count >= 1 and neg_count == 0:
        return 1  # Positive
    elif neg_count >= 1 and pos_count == 0:
        return 0  # Negative
    else:
        # Check for neutrality
        neutral_count = sum(1 for word in tokens if word in neutral_words)
        if neutral_count > pos_count + neg_count:
            return 2 # Neutral
        return model_prediction

def predict_paragraph(paragraph):
    """
    Predicts the sentiment of a full paragraph, providing counts for positive and negative words.
    """
    processed_text = preprocess_text(paragraph)
    tokens = processed_text.split()
    pos_count = sum(1 for word in tokens if word in positive_words)
    neg_count = sum(1 for word in tokens if word in negative_words)

    prediction = hybrid_predict(paragraph)

    if prediction == 1:
        sentiment_label = "Positive"
    elif prediction == 0:
        sentiment_label = "Negative"
    else:
        sentiment_label = "Neutral"

    return pos_count, neg_count, sentiment_label


training_data_raw = [
    ("Orí wo ibi rere gbé mi dé, ẹsẹ̀ wo ibi rere sìn mí yà. Ibi yà lọ́nà mi, ire kò mí lọ́nà, ẹ̀bẹ̀ mo bẹ̀ Orí Àtètè ríran.", 1),
    ("Ìwọ ikú òpònú abaradúdú wọ, o ò ṣe é 're o. O d'óró, o ṣ'èkà, o m'ẹ́ni rere lọ. Bàbá wọn ṣe bẹ́ẹ̀ ó lọ.", 0),
    ("Ọmọ bàbá Fẹlá, àti àwọn ẹlẹgbẹ́ẹ rẹ̀ ní kí ẹ pàdé àwọn ní fún", 2),
    ("Oṣù kejì ọdún ní í s'ọdún di akọ ọdún. Ọdún mẹ́rin mẹ́rin akọ ọdún ni 2016, irúu rẹ̀ tún di 2020. Elédùmarè yóò pa wá mọ́.", 1),
    ("Àyà wanle bí òkú ìbànújẹ́", 0),
    ("Bíbíre kò ṣeé fi owó rà", 2),
    ("E se mo dupe a o ma ri ire ba ara wa se, okun Ife to wa laarin wa ko si nii ja lailai", 1),
    ("Ọmọlọ́mọ là á rán níṣẹ́ à á dé lóru, ẹ wí fún wọ́n pé kí wọ́n ó rán'mọ wọn. Wọ́n kì í múyan síi.", 0),
    ("Kíni orúkọ ẹja yìí?", 2),
    ("“Ohun tó máa ṣẹlẹ̀ séyàn máa ńgbọ́n ju èyàn lọ ni, béeni, òfo eni kìí se elòmíràn kí oba òkè s'àánú wa.” ah! Ayé yìí!", 1),
    ("asa kasa ti awon eyan ko ni odo awon oyinbo tiko mu ogbon wa, koda rara,atipe ounse okunfa alebu ati arun", 0),
    ("ÌKỌ́KỌRẸ́, oúnjẹ àwọn Ìjẹ̀bú. Wọn lè fi ẹja gbígbẹ, edé, pọ̀ǹmọ́, ẹran gbe lárugẹ. Ó dùn jẹ pẹ̀lú ẹ̀bà tútù.", 2),
    ("A ò lè torí ayé dayé ọ̀làjú kí a máa f'ojú egbò gbo ilẹ̀. Ì-ṣẹ̀-ṣe làgbà, ẹ máà jẹ́ a dà á nù bí omi ìṣanwó.", 1),
    ("Mo ń rí àwọn èébú kọ̀ọ̀kan. Àti àwọn tí wọ́n ń fi wá ṣe yẹ̀yẹ́. Ẹ fiwọ́n sílẹ̀, ara ló ń ta wọ́n.", 0),
    ("Shroud ni àkójọpọ̀ àwọn ẹja lédèe Gẹ̀ẹ́sì, kí ni àkójọpọ̀ ẹja nínú omi lédèe Yoòbá? A. Ìgẹ̀rẹ̀ B. Ìwẹ̀ D. Agọ̀", 2),
    ("Toò. Ẹṣeun arábìnrin wa. A jẹ́ pé Ọba Ṣèyíówùú ni Ẹdùmàrè. Ó hàn gedegbe bẹ́ẹ̀. Adúpẹ́", 1),
    ("Ọ̀rọ̀ wo ló wà lẹ́nu bàbá Ìyábọ̀ gan àn? Kí ni Ọbásanjọ́ ń wò o?", 0),
    ("A ti wà ní gbàgede ní", 2),
    ("Ojúmọ́ ti mọ́. Ojúmọ́ ti mọ́ mi nílẹ̀ yìí o. Ojúmọ́ ti mọ́. Mo ríre o!", 1),
    ("nkan ti bàjẹ́ pátá pátá pátá ní !. Àbí báwo ni wọ́n ṣe tún jẹ́ kí DanaAir padà?", 0),
    ("Ẹṣin ọ̀rọ̀ àwọn bàbáa wa kan ní: àgò l'ó máa dé ẹdìẹ gbẹ́yìn. Àwòrán àgò inú òwe nì rè é.", 2),
    ("Ẹmọ́ jíire lópòó'lé, àfèèbòjò jíire ní'sà rẹ̀. Emi náà ti jíire lónìí o. Mojúbà Olódùmarè.", 1),
    ("Àdánìkànrìn ejò ló ń jẹ ọmọ ejò níyà", 0),
    ("ARUGBÁ Ọ̀SUN jẹ́ ọmọbìnrin tí ó wá láti ìran ÀTAỌJÀ ÒṢOGBO. Ọmọbìnrin náà gbọ́dọ̀ jẹ́ wúńdíá, fún ìgbà tí ó ma fi jẹ ARUGBÁ. Ó ma jẹ́ arugba fún ọdún díẹ̀, títí wọ́n ma fi yàǹda rẹ̀ tí ó bá dàgbà, láti ní ọkọ.", 2),
    ("Amin Oo! Ki ori wa di ori Apesin.", 1),
    ("Ẹdun àrá Ṣàngó ní ń sán pa olè àti ọlọ́kàánjúà t'ó jíṣu láti fi gún'yán, onítọ̀hún yó jẹyán rẹ̀ níṣu.", 0),
    ("Ọ̀rọ̀ ni ọ̀rọ̀ ń jẹ", 2),
    ("nípa akitiyan nínú orílè̟-èdè àti ìfo̟wó̟s̟owó̟ pò̟ láàrin àwo̟n orílè̟-èdè ní ìbámu pè̟lú ètò àti ohun àlùmó̟nì orílè̟-èdè kò̟ò̟kan.", 1),
    ("Bi awon Ologbon ba kuna lati ja fun ipo ninu isakoso Ilu,Ogbon omugo ni won o fi dari won", 0),
    ("Òjò náà wá yàgò fún oòrùn", 2),
    ("Títóbilolúwa.", 1),
    ("Emo wolu Iwo ni Ipinle Osun. ọba ti fe ja si oja, e mu so o, ki Oba alade ile Yoruba ma so isokuso pe Oluwo ilu Iwo ti di oye itan, Akanbi ti yi Oye Oluiwo si Emir ile Yoruba. Nje ko kin se aisan opolo lo ya wo aafin Oluiwo ilu iwo bayi?", 0),
    ("Bí Ọlọ́run bá fẹ́ẹ́ bá wọn sọ̀rọ̀, Ọlọ́run lè kàn fi èrò náà sí ọkàn wọn,", 2),
    ("tí ìdarapọ̀ sì ṣí sílẹ̀ fún gbogbo obìnrin. Ẹgbẹ́ náà jìjà ìgbara lórí owó orí àìtọ́ tí wọ́n fi lé orí àwọn obìnrin ọlọ́jà pẹ̀lú owó àìtọ́ lórí ọjà. Olúfúnmiláyọ̀ fi ipò rẹ̀ gẹ́gẹ́ bíi Ààrẹ ẹgbẹ́ náà, jà fún ẹ̀tọ́ kan náà fún obìnrin àti ọkùnrin àti ìwà", 1),
    ("Sebi agbejoro ni wan pe ologbeni yi, se ti oba de ile ejo, ariwo PROCESSING ni oma ma pa fun adajo? Oro yin su mi o", 0),
    ("Ọọ̀ni ò gbọdọ̀ jáde nínú ìyẹ̀wù fún ọjọ́ márùn-ùn, òun pẹ̀lú Àgbààgbà méje ní iṣẹ́ láti ṣe.", 2),
    ("Ìwúre kan tí àwọn Yorùbá máa ń ṣe ni:mi ò ní kú, mi ò ní rùn, mi ò ní fi ara gbàrùwẹ̀.", 1),
    ("Ó ti wà bẹ́ẹ̀ lọ́jọ́ t'ó ti pẹ́. Olóògbé bàbá Alfredo Darrington Bowman tí àwọn èèyàn mọ̀ sí Dr. Sebi ti ilé iṣẹ́ ìwádìí USHA ní America ṣe àfihàn àwọn oúnjẹ ikú wọ̀nyí. Kódà, ọ̀ràn náà só síni lẹ́nu, ó tún buyọ̀ sí i. Nítorí owó", 0),
    ("O fẹ́ pọ́nrán tó ki pọ́pọ́, gùn bíi tẹṣin? Àgbò tí a fi pándọ̀rọ̀ to èlò rẹ̀ ló lè ṣe é. A ó gún n, pò ó mọ́ orí, fi wọ́ okó.", 2),
    ("A ku ose tuntun. Ire owo, ire omo ati aiku ti nse baale oro ninu ose yii oo!", 1),
    ("Mo ṣàkíyèsí kan. Bí mo bá túwíìtì nípa ìṣẹ̀ṣe, ara àwọn kan kì í gbà á, wọ́n á ṣíra tẹ àìbárìn, wọn kò tẹ̀lé mi mọ́. Òtítọ́ a máa korò. Kò sì sí bí a ó ti se ebòlò tí kò ní rùn, kò sí bí a ó ti sọ̀rọ̀ ìran Yoòbá tí a ó yọ t'òòṣà kúrò, kò ṣe é ṣe.", 0),
    ("Ta l'o mo oluraja tiles ile ati ogiri, ti o fe maa raa lati orile ede China. Ile ise ti o nse TILE ni mo", 2),
    ("Ibi tí a ńlọ là ńwò, a kì í wo ibi tí a ti ṣubú.", 1),
    ("Operekete ndagba, Inu Omo Adamo nbaje. A di Baba tan Inu nbi won.", 0),
    ("Ṣé o mọ̀ pé ilẹ̀ tí a fún àwọn ẹrú agbòmìnira láti ni SaroTown tí ó wà ní LagosIsland?", 2),
    ("Jesu dáhùn ó sì wí fún un pé, “Lóòótọ́ lóòótọ́ ni mo wí fún ọ, bí kò ṣe pé a tún ènìyàn bí, òun kò lè rí ìjọba Ọlọ́run.", 1),
    ("ọdún méjì ni àmodi fi ṣe é", 0),
    ("Eni ijaoba níí pe ara rẹ̀ ní ọkùnrin", 2),
    ("Rọra ṣe o, rọra ṣe. Ọmọ ẹ̀mí rọra ma ṣe.", 1),
    ("Alárìnká, ajẹlójú-onílé náà ni à ń pe èkùté-ilé.", 0),
    ("Ǹjẹ́ o mọ̀ wípé ìnagijẹ àwọn ọmọ ìyá wa t'ó ti oko ẹrú Brazil dé ni Àgùdà? Agbègbè tí a fún wọn gbé ló di Pópó Àgùdà.", 2),
    ("Òmìnira ọ̀rọ̀. Òmìnira ìrin gẹ́gẹ́ bí ọmọ ìlú. lẹ́tọ̀ọ́ sí òmìnira ara rẹ̀", 1),
    ("Ese kọ́ l'ọmọdé àkọ́kọ́ t'áwọn bíi Yinusa ńfi s'ábẹ́. Òfin'lẹ̀ wa f'àyè gbàgbàkugbà, ara ìwà pálapàla tía kọ́ nù n.", 0),
    ("hahahaha. Ti ayé àtijọ́ mà ni o. Bí wọ́n ti nṣe kí àwọn òyìnbó àti Lárúbáwá tó dé.", 2),
    ("Abẹ́rẹ́ á lọ kí ọ̀nà okùn tó dí. Ibi gbogbo tí ń bẹ lọ́nà, ẹ bìlà, ọmọ ọlọ́nà ń bọ̀. Ẹ̀gbá ẹ kú àlejò mi o!", 1),
    ("Awon agbogunro ya wo ile Senator Bayo Salami ti o hun se asofin Olorunda ni Ile Asofin ni Abuja", 0),
    ("Ní ayé àtijọ́, kí ẹ̀sìn titun tó ó gòkè odò ni àlàálẹ̀ ọ̀nà ìgbé ayé ti ń bẹ bí ẹ̀bẹ.", 2),
    ("Orí ẹni làwúre ẹni. Bí a bá jí lówùúrọ̀, ká gbá Oríi wa mú. Nítorí Orí ẹni ni àpere ẹni. Orí ẹni àpésìn. Orí ẹni là bá bọ.", 1),
    ("Ede gesi yin gan o gbadun! Ewo ni right write ni sir! Eti fi owo awan obi yin Jona!", 0),
    ("Mo gbọ́ pé ìgbìmọ̀ kan ń jókòó lórí ọ̀rọ̀ yìí, ṣé òtítọ́ ni?", 2),
    ("Aseyi Shamodun lagbara Edumare Amii àṣẹ", 1),
    ("Ẹranko tó bá ṣiyèméjì lọde ńpa.", 0),
    ("Orò ló ni àròpe Ọdẹ ló sun ìjálá Ìyẹ̀rẹ̀ n t'Ifá ẹ̀sà ni ti egúngún", 2),
    ("À ń jáde lọ lónìí Elédùmarè...Dáàbòbò wá.", 1),
    ("esa fe ti ina bo ile Yoruba tipa tikuku. Ari ijamba ti awon egbe Ganiyu Adams se ni ilu eko lojo aje. Eledumare yio da yin lejo", 0),
    ("Obìnrin ẹfọ̀n sì fún un lésì pé àwọ̀ òun tó òun gbé pamọ́ lòun ń wá.", 2),
    ("Ẹdákun ẹ bá wa ṣe kiní ẹ̀rọ ọ̀ọ̀mọ̀ yìí kí a lè dìbò níbikíbi tí a bá wà, kò báà ṣe ní Kutuwenje tàbí Kanfansa.", 1),
    ("Àwọn gómìnà ń ṣe ìgbéyàwó fọ́mọ wọn nígbà tí Boko Haram ń ko àwa lọmọ lọ", 0),
    ("Be ni o Njẹ́ ojúmọ́ kan kìí mọ́ bí kìí ṣe agbára Ọlọ́run.", 2),
    ("Obì àti akèrègbè ẹmu ni a ó gbè é dání láti fi bẹ awo kí ó bá wọn de oyún kí ó má báa wálẹ̀.", 1),
    ("Aiye le: Obirin loyun fun oko re, lo ba dana si ile won pelu oun ati oko re ninu e", 0),
    ("1,674 ọkọ̀ l'ó wọ Newcastle. Àjàyí Crowther náà fi òtùtù òwú ìlú Abéòkúta ṣọwọ́ sí Manchester ní ọdún 1851.", 2),
    ("amin. A ku owuro, ojumọ ire lo mọ ba wa loni.", 1),
    ("10 kọbọ mi to jabọ! to jabọ!! to jabọ!!! 10 kọbọ mi to jabọ! Nigeria lo o mu 🇳🇬", 0),
    ("Ǹjẹ́ ìwọ́ mọ̀ wípé Ilé-Ifẹ̀ ti lo onírúurú sáà sẹ́yìn kí ó tó kan Ifẹ̀ òní? * Otù Ifẹ̀ * Ifẹ̀ Oòdáyé * Ifẹ̀ Oòrè * Ifẹ̀…", 2),
    ("Ẹ nlẹ́ o. Ẹ kú ọjọ́ gbọgbọrọ bí ọwọ́ aṣọ.", 1),
    ("yi go sa! Ewo bi o se pon le. Onijekuje igba wo ni ti o ponle di ota e?", 0),
    ("B'ó jẹ́ ẹ̀tọ́ bíi baba ni, ẹ̀tọ́ ọkọláyà, ẹ̀tọ́ orí ẹní, ẹ̀tọ́ àbò ẹbí.", 2),
    ("Ayélujára ti ṣ'ayé d'ẹ̀rò. Gba ìdanilẹ́kọ̀ọ́ lórí ayélujára. Èmi náà ń gba ìdanilẹ́kọ̀ọ́ níbẹ̀.", 1),
    ("Ọ̀pọ̀ èèyàn wòde, a ò mọ ẹni t'ó gbé ọmọ Ọbà fún Ọ̀ṣun. Àtọ̀húnrìnwá ló pọ̀ ń'nú àwọn ọmọ gànfé tí à ń wí wọnyìí.", 0),
    ("Èyí ni ewé àfòmọ́. 1. A óò sá a ní oòrùn, yóò gbẹ dáadáa, a óò lọ̀ ọ́ kúnná, 2. Kí ẹni tí ó bá ní àrùn rọ́parọsẹ̀ ó máa…", 2),
    ("Ni iranti baba wa Adebayo Faleti fu ise ti wan se fu èdè wa", 1),
    ("Arugbo koni daa o. Kilode", 0),
    ("Ewé ọmurun wà, ewé gbégbé, gbòdògì, iran àti bẹ́ẹ̀ bẹ́ẹ̀ lọ ò gbẹ́hìn fún oúnjẹ wíwé.", 2),
    ("Eyin Ọpẹ́yẹmí funfun báláú/ṣéṣé/pìn-ìn", 1),
    ("Awọn aṣiwere Ye", 0),
    ("ní. Ó ní àgbẹ̀ náà lè wọ ago Rolex, pé kí àwọn ọ̀dọ́ ó ṣe àgbẹ̀", 2),
    ("Ọ̀sẹ̀ tuntun wọlé. Kí Ọlọ́run Ọba ṣe amọ̀nà wa.", 1),
    ("Bamitale ati Oluwasegun rewon he l'Ondo, oba alaye ni won fee ji gbe - Alaroye", 0),
    ("Tó bá di ìrọ̀lẹ́, màá yà gba ọ̀kan ń'nú àwọn àdúgbò yẹn. Màá gbé àwòrán ẹ̀ sáyé fún yín.", 2),
    ("Yoruba ronu ooo ..", 1),
    ("Ó jọ pé wọ́n ò fẹ́ a dàgbà, ni wọ́n ṣe ń dá ẹ̀míi wa légbodò. Torí bí BH pa ọ̀dọ́ kan, gbogbo ọ̀dọ́ lọ́ pa", 0),
    ("Ní báyìí ó ti di ibi-ìpéjọ fún ìkójọ àti ọ̀rọ̀. Báyìí, ìbéèrè wọ̀nyí ṣe kókó bí a bá ń lo ẹ̀rọ-alátagbà: Báwo ni mo ṣe lè lo ẹ̀rọ-alátagbà wọ̀nyí nípasẹ̀ bẹ́ẹ̀ dáàbò araà mi? Ibi-ìkọ̀kọ̀ mi? Ìdánimọ̀ọ mi?", 2),
    ("Eda to mo ise okunkun ko ma da osupa loro, nitori eni la ri, Oluwa Oba lo mo ola", 1),
    ("Òròmọadìyẹ ńbá àṣá ṣeré, ó rò pé ẹyẹ oko lásán ni.", 0),
    ("Ó dẹ̀jì. Tí a bá ka iyé àwọn akọ̀wé Gẹ̀ẹ́sì ní ilẹ̀ Yorùbá, á máà lọ bí ẹgbẹ̀rún mélòókan.", 2),
    ("Lẹ́hìn òkùnkùn biribiri, ìmọ́lẹ̀ á tàn.", 1),
    ("Oorun jọ ikú, ikú jọ oorun, bẹ́ẹ̀, ìkan sunwọ̀n jù 'kan. Oorun ìyè àti oorun ikú ni oorun méjèèjì ń jẹ́.", 0),
    ("Oko baba ẹni kì í tóbi kí ó máà ní ààlà.", 2),
    ("Ó ku ọ̀ṣẹ̀ kan kí a dìbò, ǹjẹ́ o ti gbaradi? O ti pinu ẹni tí o ó dìbò rẹ fún, wolẹ̀ kí o tó tẹ̀ka, ronú kí o tó dìbò.", 1),
    ("Àwa mà nìyẹn o. Àfi kí Elédùà kówa yọ. Gbàù! lónìí gbòsà! lọ́la yìí fẹ́ pọ̀ díẹ̀.", 0),
    ("idi keji wa n ko o?", 2),
    ("E re gbe wa bi /x2, Eyin te se gbe yin basu-basu, E re gbe wa bi?", 1),
    ("Nígbà tí ó máa fi di ìdájí ọjọ́ Ajé, ìròyín ti kàn wípé àwọn ọ̀tá ti ń sún mọ́. Nígbà tí ọ̀sán pọ́n, ìró ìbọn ti gba afẹ́fẹ́, èyí ti kéde wípé ogún ti bẹ̀rẹ̀.", 0),
    ("Fùkù ni ẹ̀yà ara tí ó ń gba afẹ́fẹ́ tí a mí sínú. A lè tún pè é ní Ẹ̀dọ̀ Fóóró", 2),
    ("mo kii yin o. Eni a san wa si ire o. A a ni sise loni o. Olorun a fun wa se", 1),
    ("Àwọn ènìyán jíyìn wí pé ìró ìbọn ṣì ń lọ ní kòṣẹkòṣẹ ní Lekki...", 0),
    ("E yon gbau! Ogbeni,bawo lose ri ere boolu afese gba to waye larin orilede wa ati iko agba boolu Ethiopia...", 2),
    ("E kaaro o omi o yale Ope ni fun Olorun", 1),
    ("Bí Ṣànpọ̀nná bá pa ènìyàn ____ ni a máa ń sọ pé ó gbé ẹni náà lọ?", 0),
    ("ó yẹ kí n ṣàlàyé pé Àkẹ̀ ni a máa ń pe àwọn ewúrẹ́ tó bá tóbi jùlọ,", 2),
    ("Mo ti PINU lórí ọ̀rọ̀ yìí wípé ọkọ̀ tuntun ni mo ma rà", 1),
    ("Àgbàrá òjò fa súnkẹrẹ fàkẹrẹ.", 0),
    ("Kò ti ẹ̀ yẹ k'á máa fọ èdè ọ̀gá rárá ni, mo ṣìkejì, ló yẹ á máa sọ.", 2),
    ("Ẹ ṣé gan A kú ọdún o", 1),
    ("Èwo lá tún gbọ́ yìí o? Wọ́n ní BokoHaram fẹ́ gbà'jọba ní ìpínlẹ̀ Yobe? Ó ga o!", 0),
    ("Fìlà Yorùbá tí ó gbajúmọ̀ sí àwọn ọlọ́dẹ, tí ó gùn, tí ó sì ṣẹ́ wá sí èjìká, ni à ń pè ní GBẸ́RÍ ỌDẸ", 2),
    ("naani naani naani, ohun a ni la naani. Tiwan ntiwa, teni nteni. A o gbodo ta lopo.", 1),
    ("Àní ká fi ọ̀rọ̀ ọ̀hún mu tábà ní gbẹ́rẹ́fu. Ọ̀rọ̀ burúkú tòun tẹ̀rín.", 0),
    ("Oruko mi ni Olanrewaju Ajayi,abi mi si Somolu ni ilu Eko aromi sa legbelegbe. Omo ilu ijagbo ni ipinle Kwara ni awon obi mi.", 2),
    ("Ẹ kú òwúrọ̀ kùtù-kùtù. Ṣé dáadáa la jí ?", 1),
    ("Tani jeun ti aja un juru, Ebenezer Babatope na un soro.... ara awon ojelu ti won tan de iparun re o", 0),
    ("Kí ló dé tí àwọn arìnrìn-àjò Mecca l'ọ́kùnrin fi máa ń pa kájà aṣọ bí ẹní wọ igbódù?", 2),
    ("Toò. Ó hàn gedegbe pé wọ́n jọ bí i yín ire ni. Ọmọlúàbí wá gba ọmọlúàbí ní àbúrò.", 1),
    ("ó tì, àwọn nǹkan wọ̀nyí ni a fi jẹ́ ìran Yorùbá. Digbí ni ìṣe yìí wà láyé ìjọ́hun, ẹ̀yìn tí òyìnbó dé ló parun.", 0),
    ("Bí a ò bá jẹun dà sí ẹ̀yìn abọ́, èèrà ò ní gun ibi tí a ti jẹun wá.", 2),
    ("Àt'ẹni k'àwé, àt'ẹni kò kà t'ó bá ti jẹ́ ọ̀ṣọ́rọ́, ó yẹ kí I.T.F ràn án lọ́wọ́", 1),
    ("Ẹní bá gúnyán tí ò fi t'Ọ̀ṣun ṣe, iyán rẹ̀ á díkókó", 0),
    ("Ọ̀RỌ̀ ÌṢÍTÍ WA T'ÒNÍ: IRUN ṢÍṢE", 2),
    ("e se mo dupe pe e ka emi naa mo awon eniyan iyi, Iyi enikankan wa ko ni di ete lailai", 1),
    ("Iyen maa le die o!", 0),
    ("Ọ̀kọ̀ọ̀kan là ń ka OwoEyo, lẹ́yìn náà, a óò wá sín in sínú okùn. Okùn owó kọ̀ọ̀kan ní orúkọ tí à ń pè é.", 2),
    ("Lẹ́yìn tí a ti gbọ́ ohùn ìyá tí a gbọ́ ohun ọmọ, ìdùnnú pẹ̀lú ayọ̀ ní í gbalẹ̀ kan, àrídunnú àríyọ̀ ni à ń rí ọmọ tuntun.", 1),
    ("Ìyá àjáàràbúkà, ó ti ọmọ mẹ́ta mọ́lé alákọrí bá àlè lọ, kí alágbèrè tóó dé, iná ọmọ ọ̀rara ti jó àwọn ọmọ tó wá jayé wọn pa.", 0),
    ("Ewúré jé eran ilé.", 2),
    ("Amin o ati eyin naa se daadaa ni", 1),
    ("Ewu nmbe loko longe ! Idamu de ba Aare orilede Nijeria.", 0),
    ("Àwọn Yorùbá gbàgbó wípé, bí àwọn èèyàn wọn tó dàgbà bá papò dà, wọ́n lè tún padà wá sí aiyé, láti ma bá wọn gbé lọ. Òhun ló ṣe jẹ́ wípé, bí òbí èèyàn bá kú, tí ọ̀kan nínú ọmọ tí wọ́n fi sílẹ̀ láyé bá bí ọmọ, wọ́n ma sọ ọmọ náà lórúkọ", 2),
    ("âṣé nǹkankan t'àgbàlagbà rí lórí ìjókòó ọmọdé ò lè rí i lórí ìdúró.", 1),
    ("Ẹ rò ó. Àgbẹ̀ ló ma yọ wá nílúu wa yìí. Kọ́mọ kàwé má rí'ṣẹ́ ṣe, àwé nǹkan jíjẹ sì ń tà wàràwàrà.", 0),
    ("Ọdún 1862, Britain ṣí ilé ìfowópamọ́ London Brazilian Bank fún oníṣòwò ẹrú.", 2),
    ("Ọmọ àjànàkú kan kìí yàrá, ọmọ tí erin bá bí erin níí jọ.", 1),
    ("Owó tí a fi ra ẹ̀kọ́ kìí lè jẹ́ kí á sọọ́ nù.", 0),
    ("Gẹ́gẹ́ bí Onígbá Iyùn ṣe dá a lábàá, wípé kí n máa sọ ìdáhùn ìbéèrè tí ẹnikẹ́ni kò bá gbà. Bí ó bá di agogo mẹ́jọ ajálẹ́ yìí, ẹ ó gba ìdáhùn síbèêrè.", 2),
    ("Lònii isinmi wa fun gbogbo osise ni ipinle Oyo, ki won Le lo gba kaadi idibo alalope won. Njè Iwo ti gba tìre naa bi?", 1),
    ("Eni ti ko ba ni'fe iya ti o bi i tokan-tokan, a padanu ibukun nla ni'le aye ẹ̀", 0),
    ("Mo fe ba e se ibalopo ogbontarigi.", 2),
    ("Ekaaro oooooo. Mo kí gbogbo yín o. Ẹ kú ọjọ́ Àìkú o. Àìkú tí í ṣe baálẹ̀ ọrọ̀.", 1),
    ("Ewure to to sinu isaasun ibi ti yoo sun ni o n baje, enia ki ba mo ibi ti yoo sun oun ko ba tun ibe se", 0),
    ("Kí ni ó ṣẹlẹ̀.", 2),
    ("A kì í dàgbà jù fún ohun tí a kò bá mọ̀.", 1),
    ("Ìpèníjà àti ìdààmú ńlá rèé fún ìran Yorùbá.", 0),
    ("àwọn obìnrin wo ọ̀nà òmíràn, láti múra, nígbà tí wọ́n gbé ìró wá sí òkè àyà wọn, èyí tí ó bo ọmú wọn dáada, ní àsìkò 1100.", 2),
    ("Ẹ jọ̀wọ́, ṣé ẹ lè fún wa ní shout out? Kí àwọn followers yín, lè mọ̀ wàá. Inú wa ma dùn, tí ẹ bá lè ṣe èyí fún wa. Ẹ ṣeun", 1),
    ("jọ, jagun. Àwọn ará Ìkòròdú fi ìdí wípé, ohun tí wọ́n fẹ́, bá ti Èkó lọ. Àti wípé, pàṣán tí àwọn Ẹ̀gbá fi na àwọn Oníṣòwò Èkó, ta bá àwọn náà ní Ìkòròdú, tí ìdáwọ́dúró ìtajà wà, látàrí ìjà tí àwọn Ẹ̀gbá ń gbé ko àwọn Oníṣòwò lójú.", 0),
    ("Wọ́n á ní “àtẹ̀ yún àtẹ̀ wá ni àtẹlẹsẹ̀ ń tẹ ekùrọ́ ojú ọ̀nà”. Kí ni ìtúmọ̀ yún nínú “àtẹ̀ yún”?", 2),
    ("amin o edumare! ki oba oke da gbogbo wa si, ki o si bu oju aanu wo orile èdè yìí…", 1),
    ("Asiko ko dẹrun fun minisita fun eto iṣuna lorilẹede Naijiria, lọwọlọwọ pẹlu iroyin kan to n ja kaakiri bayii pe ayederu ni iwe ẹri agunbanirọ ti o n gbe kiri.", 0),
    ("Láílo láílo! Láílo, ọmọ ìyá mẹ́ta ... ", 2),
    ("Lónìí ni kò ní d'ọ̀la. Ó ti tó gẹ́! Kò s'ẹ́ni t'ó lé pa ohùn mọ́ agogo lẹ́nu, ẹ kò leè pa ohùn mọ́ òmìnira lẹ́nu. Ìwé ìfisùn tí 100, 000 èèyàn fọwọ́ bọ̀ yóò tẹ àwọn ìgbìmọ̀ aṣòfin lọ́wọ́.", 1),
    ("Látorí àṣà 'kú/ẹ kú' tí àwọn ọmọ ìyá wa tó lọ sóko ẹrú nílẹ̀ Amẹ́ríkà ni a fi sọ ìran Yorùbá ní Akú.", 0),
    ("Ọjọ́ kẹta ni ọjọ́ Ògún; Oṣoosì. Ọjọ́ kẹrin sì ni fún òòṣà Ṣàǹgó; Ọya.", 2),
    ("Ẹlòmíràn yan Orí ẹran ìfẹ́ láti ọ̀run wá. Irú ẹni bẹ́ẹ̀ ni wọ́n ń máa ńsọ pé 'ó lẹ́ran ìfẹ́ lára. Ó nífẹ̀ẹ́ èèyàn, èèyàn nífẹ̀ẹ́ rẹ.", 1),
    ("Ìjọba ìgbàlódé ń bá ìjọ ọba àdáyébá. Kò yẹ kí èyí ó wáyé rárá àti rárá ni. Àwọn ará ibí kàn ń sọ ìṣẹ̀ṣe di yẹpẹrẹ ni.", 0),
    ("Mo ti mo tele pe Atiku maa kuro ninu egbe APC", 2),
    ("Abi oo. T'oba pe taa rira,eku ati lan k'ira. Ẹ kú àti ẹ̀yin èèyàn mi. Ṣé gbogbo ẹ̀ ń lọ déédé? ó tó'jọ́ mẹ́ta.", 1),
    ("Àbùkù ti kan ọmọ náà.", 0),
    ("Eni to ba ni oyun", 2),
    ("Ayọ̀ àti àláfíà ni o, ọmọ ìyá mi. ẹ̀yin nkọ́?", 1),
    ("Àwa ènìyàn dúdú pàápàá bẹ̀rẹ̀ sí í bára wa jagun, a sì í ńtara wa lẹ́rú fún èèbó nítorí owó.", 0),
    ("Aṣọ ẹ̀yẹ ìkẹhìn tí ọmọlẹ́bí fi fún òkú, tí òkú yíó gbé wọ ibi-ojì ni aṣọ-ẹbí.", 2),
    ("Òtútù yìí ga. ẹ tún ti sa kuro nibi? S'alafia le wa? O to jo meta o..", 1),
    ("À rí ìgbọdọ̀ wí, baálé ilé sú 'ápẹ.", 0),
    ("Àjọ̀dún wo rè é ní Ọ̀ṣun, Ilé-Ifẹ̀?", 2),
    ("Amin o mo dupe e ku igbadun ilu wa yii o emi naa ti n tele yin o, a ko ni tele ara wa wo inu iparun o! E kaaro.", 1),
    ("Ó ga o! Ọ̀gá kílódé? Kí lẹ fẹ́ fi ọkọ̀ olówó iyebíye bá'un ṣe? Ta lo ṣẹ̀?", 0),
    ("Njẹ o mọ pe olugbe nla Yoruba wa ni ilu Brazil ti wọn n sọ ede Yoruba ti wọn si n ṣe aṣa Yoruba?", 2),
    ("ese, onise yin ti je o", 1),
    ("Gbogbo ilé-iṣẹ́ wa wá di gbájúẹ̀. Ẹ̀rọ ìbánisọ̀rọ̀ ò dún dé ọ̀dọ̀ ẹni a pè, àmọ́ wọ́n yọ owó fùkẹ̀ lápò wa.", 0),
    ("sí ibẹ̀, kí ó kú, lẹ́hìn tí wọ́n ti gé ara rẹ̀ bàjẹ́. Ṣùgbọ́n, ó yè, ó sì wọ́ lọ sí inú igbó. Ó tiraka láti wà láyé, tí ó sì yè lórí jíjẹ èso nínú igbó. Lẹ́hìn ti ara rẹ̀ ṣe gírí, ó di àgbẹ̀ Àyè ṣí sílẹ̀ fún láti pàdé àwọn èèyàn kan nínú abúlé kan.", 2),
    ("Ọdún tí nbọ̀ yìí, ire ni fún gbogbo wa. Ọdún tó bẹ̀rẹ̀ ní ọ̀la, ọdún ọlá, ọdún ọlà!", 1),
    ("Ni òwúrọ̀ kùtùkùtù ọjọ́ kan, ó tọ́ ìyá-a rẹ̀ lọ láti ṣ'àlàyé ọ̀ràn náà tí ojú-u rẹ̀ ń rí nílé ọkọ. Ó sọ fún ìyá-a rẹ̀, wípé ọ̀rọ̀ ọkọ òun ti sú òun, wípé òun kò leè farada ìhùwàsíi rẹ̀ mọ́.", 0),
    ("Àwọn wọ̀nyí àt'àwọn abọ́bakú ni wọn yóò máa ṣe ìránṣẹ́ ọba lọ́hún (ọ̀run).", 2),
    ("A kú ojúmọ́ o.", 1),
    ("Ara àntí ò yá Ara àntí ò yá Ìkọ́kọrẹ́ ń wọlé, abọ́ ń jáde.", 0),
    ("Ǹjẹ́ ìwọ́ mọ̀ wípé Afrospot (Empire Hotel) ní ẹ̀gbẹ́ ilée Fẹlá ni ó di ilé Ijó Afrika Shrine àkọ́kọ́ fún orin Fẹlá? Kànmí Ìṣọ̀lá, ọ̀rẹ́ẹ Fẹlá Aníkúlápò Kútì ni ó sì pe Afrospot ní Afrika Shrine.", 2),
    ("Toò. Ìpàdé wa bí oyin o.", 1),
    ("Ilé tí a f'itọ́ mọ; ìrì ni yóò wó o. *Báwo ni ilé tí a fi itọ́ ẹnu mọ ṣe fẹ́ dúró sánsán? Bí ìrí bá ṣẹ̀, ó di gbàgà!", 0),
    ("Ìdúró àti ìjókòó, ìró àti ibú, rẹwà àti__, ga àti kúrú.", 2),
    ("Wọ́n ti kọ́ ọ̀pọ̀lọpọ̀ ilé iṣẹ́ tuntun sí ìpínlẹ̀ Ondo", 1),
    ("lábẹ́ Ọ̀gbómọ̀ṣọ́. Gbọ́n'mi si, omi ò tòó kan ṣẹlẹ̀ láàárín Tìmí Ẹdẹ àti Kakanfò Ọ̀gbómọ̀ṣọ́. Ohun tó fà áwọ̀ yìí, kò fojú hàn. Kakanfò fi Ẹdẹ ṣí Ẹtù tí Kìnnìún kò gbọdọ̀ ma ṣ'ọdẹ rẹ̀. Ni ó bá fi ìjà náà lé Lásinmi, tíì ṣe Balógun rẹ̀ lọ́wọ́.", 0),
    ("Mo ti tẹ̀lé yín o, bí eṣiṣi ṣe ń tẹ̀lé elégbò", 2),
    ("Ẹ kú ti ìlú wa. Ẹ dẹ̀ kú ti Ebola tí ò fẹ́ kí a máa f'aranura, f'arakanra, k'á báraa wa ṣe, k'á kórajọ . Ọlọ́run á máa sọ́ wa", 1),
    ("Àwọn ará ibí yìí mọhun tí wọ́n ń ṣe o, bí wọ́n fún-un yín ní kọ́bọ̀ kí wọ́n tó wọlé, Náírà ni wọn yó fi kó bí wọ́n débẹ̀ tán.", 0),
    ("Mi o mo won o, sugbon mo l'ero pe Rev Dandeson Crowther omo e, ati Rev T. B Macauley, oko omo e ti o bi ni.", 2),
    ("kin fun rami latewo abi? Ese gan ni", 1),
    ("Ìgárá ọlọ́ṣà gba ọkọ̀ ayọ́kẹ́lẹ́ RBC 212 DE HONDA ACCORD SILVER COLOR 2012 ọ̀rẹ́ẹ̀ mi ní Ọ̀bà-Ilé.", 0),
    ("Ẹ̀dá kàn ntiraka ni, a ò lè kọ́lé kó ga títí kó dókè ọ̀run.", 2),
    ("Fẹ̀ẹ̀rẹ̀ fẹ́ ẹ̀ẹ́ mọ́, Olúwa jí wa re", 1),
    ("Ohun tí wọ́n gbé sí alákọrí lórí nìkan ló mọ̀, ó rò wípé a ò tí ì máa ka ọjọ́ kí ọlọ́ṣà tó ó dé.", 0),
    ("Igba - Time Igba - Calabash Igba - Two hundred Igba - Garden Egg Ogun - Medicine Ogun - Twenty Ogun - Charm Ogun - Property Ogun - Long ó gun - Wailing Ogun - Yoruba Mythical Iron Deity.", 2),
    ("Kọ́ ọ nítorí àwọn ọmọ rẹ, kí wọ́n ba mọ̀ ọ́.", 1),
    ("Ẹbọ ní ńpa ẹlẹ́bọ...”èpè ní ńpa elépè", 0),
    ("Tori akata, l’a fid a yangan, tori eya l’aa ko yanju.", 2),
    ("Tani tabi Kini oke nla ti o do ju ko o bi iṣoro/idaamu/Apata ninu aye ati ẹbi rẹ, Olodumare yoo fi gbogbo wọn le ọ lọ wọ ni osù yii ni Orukọ Jesu.", 1),
    ("Ọ̀bẹ ń wó ilé araa rẹ̀, ó ní òun ń ba àkọ̀ nínú jẹ́. Àdá l'ẹnu tálákà, igbó la ó fi dá.", 0),
    ("Bi o ba ni idi obinrin o ki n je kumolu", 2),
    ("Ọba Yárábì tún ṣọlá Ó tún jí wa're lónìí o!", 1),
    ("Kukuru bilisi. Emo wo ilu Ado Ekiti Gomina lola ya igbaju gbigbona lu adajo ni Kotuu. Fayose wipe ohun ba adajo da apara ni..", 0),
    ("Kò sí ohun tí ẹ̀dá lè ṣe láì má fi ti ìṣẹ̀ṣẹ ṣe, ìṣẹ̀ṣẹ làgbà. Orí ìṣẹ̀ṣẹ ni ohun gbogbó dúró lé.", 2),
    ("Mo gbiyanju lati jeki fidio yi je iseju kan ni aimoye igba, sugbon kosese...E mase dami lejo fifowo nigba meta bo ti le jepe mo so wipe igba marun . E jeki a sa bojuto ara wa, olufe wa ati awon ara ile wa...", 1),
    ("hahaha. ó di dandan. Àyàfi ti èèyan bá fẹ jẹ̀jẹkújẹ kú lókù :)", 0),
    ("Oorun ti n yo ni Ile Ife, ibi ti ojumo ti n mo wa Ile aye.", 2),
    ("Ẹkú iṣẹ́ o!!! Mo fẹ́ràn bí ẹ ṣe lo àwọn àwòrán ṣe àpèjúwèé.", 1),
    ("Ohun t'ó wá jẹ́ ẹ̀dùn ọkàn fún mi ò ju pé, tíí ṣe ọ̀kan lára ohun èlòo ńkọ iyán kére.", 0),
    ("Àgbẹ̀ àti àwọn obìnrin atajà ni òfin yìí kọ́kọ́ mú, àṣẹ̀hìnwá, ó di dandan fún obìnrin nìkan.", 2),
    ("Ẹ jẹ́ k'á tẹpẹlẹ mọ́ ètò ìdàgbàsókè fún ìlú olókìkí yìí kí ògo wa máà wọmi, ẹ jẹ́ a fa ara wa sókè.", 1),
    ("Awọn ọna Meji - Ẹniti o ba gba a gbọ ko ni da lẹbi; ṣugbọn ẹniti ko ba gba a gbọ lẹbi tẹlẹ, nitori ko gbagbọ ni orukọ Ọmọ bíbi kanṣoṣo ti Ọlọrun.", 0),
    ("Ní ilẹ̀ Yorùbá àtijọ́, oríṣi owó ẹyọ méjì ló wà: èyí tí a dá ìwò sí, láti tòó pọ̀ ní ojú kan, tí a sì ń fi ṣe rírà àti títà (èyí ni owó ẹyọ. àwọn wọ̀nyìí ni wọ́n ń lò fún ìlò ẹṣin (èyí ni Owó Ẹ̀rọ̀).", 2),
    ("Ẹ ye é ba orúkọ Yoòbá jẹ́, ẹ̀yin aráa wa lórí ayélujára.", 1),
    ("Awon Adajo Ekiti ti dase sile o! Wan ni ewun be pelu awon jandukun ti ko dasi igboro. Kunmo ati Ada ti kun igboro Ado", 0),
    ("Ìlànà ẹbu náà ò gbẹ́yìn. Bẹ́ẹ̀ náà ni a tún máa ń ṣe àgbo ni àgùnmu, ẹ̀kọ ni a fi ń tì í sọ́hùn-ún.", 2),
    ("A kì í kó irin méjì bọná lẹ́ẹ̀kannáà...", 1),
    ("Oro odun lenu ole, se odun 2016 ni David Mark mo ono Agatu. Lati odun ti wan fi un pa ara won, Mark de fila mawobe", 0),
    ("Òrùn kò pa mí rí, Òjò kò pa mí rí, Mo kúrú, mo ga, Mo sanra, mo sì tírín, Kò sí ẹni tí kò ni mi. Ki ni mi?", 2),
    ("Kí ire lọ sọ́dọ̀ ẹni sọ're si mí. Arugiṣẹ́gi t'ó bá ṣẹ́gi ọ̀ràn, orí ara rẹ̀ ni yó fi gbé e.", 1),
    ("Ará Èkó ò mọyì ará oko", 0),
    ("Èwo nínú ìwọ̀nyí ni a fi ń pa owó mọ́? 1. Oko tòbí (yerí) 2. ìgbànú 3. kóló", 2),
    ("Mo dupẹ lọwọ rẹ", 1),
    ("Ọ̀gá fi ọgbọ́n àrékérekè ọwọ́ wọn ba ti wa jẹ́, àmọ́ kò yé ọ̀pọ̀lọpọ̀ wa bẹ́ẹ̀ ẹni ire la pè wọ́n, ẹni ègbé ẹni ẹ̀tàn ni wọ́n.", 0),
    ("ILÀ PÉLÉ: Ilà yìí jẹ́ àmì mẹ́ta tí wọ́n ma fà sí ẹ̀kẹ́ èèyàn. Àwọn ará Ifẹ̀, Ìjẹ̀bú àti Ìjẹ̀sà lọ ma ń já pélé", 2),
    ("Yoòbá tún wípé Ọmọdé gbón Àgbà gbọ́n ni wọ́n fi dá'lẹ̀ Ifẹ̀. Dandan ni kí tọmọdé-tàgbà kópa nínú àtúnṣe yìí", 1),
    ("Ó ti dójú ẹ̀ kí ọlọ́pàá ó máa ná owóo mọ́tò. Kódà ó bẹ̀bẹ̀ san ₦100 ni, kí àwọn ó jọ pín in ní fífítí fifitì. Kòró ká apá ẹ̀fíríbọdì, títí kan àwọn aṣebíológun àti ológun tí kì í fẹ́ sanwó ọkọ̀ l'Ékòó.", 0),
    ("O jẹ́ mọ̀ wípé kò sóhun tuntun lábẹ́ ọ̀run! Ohun tí ó ti wà tẹ́lẹ̀ ni a ti mú nǹkan òde òní. Àfikún mọ́ nǹkan tẹ́lẹ̀ ló di tuntun.", 2),
    ("Iṣẹ́ ni ọ̀pọ̀ ènìyàn fẹ́, ìdá 19% ní iṣẹ́ àwọn fẹ́ kí ààrẹ Jonathan ó tẹpá mọ́. 17% fẹ́ kí iná mànàmáná ó dúró.", 1),
    ("E kaaaro o. Emi ke? Bawo la se pin itan elede kan Lemoomu o?", 0),
    ("Àwọn awo yóò mú èèrún ara aláìsàn, aṣọ tí aláìsàn wọ̀, wọ́n á kó o sínú ìkòkò dúdú kan.", 2),
    ("Ẹ jẹ́ kí a borí ẹ̀fọn", 1),
    ("Kòkòrò tí ń j'ẹ̀fọ́, ara ẹ̀fọ́ ló wà.", 0),
    ("Àṣà ìdábẹ́ ti ṣe díẹ̀ ńlẹ̀ẹ Yorùbá, ta ni ẹni àkọ́kọ́ tí a dá abẹ́ fún?", 2),
    ("Orí, wò ibi rere gbé mi dé, ẹsẹ̀ wo ibi ire sìn mí yà. Nítorí orí ni ẹjá fi ń la ibú jà, nítorí orí ni àkèré fi ń wẹ̀ ni odò", 1),
    ("Odaran ni Matthew yii o ! O si tun fee dogbon gbe igbo wole fawon elewon", 0),
    ("Àgbà náà l'ó tún sọ pé Ṣàngó l'ó ni ṣẹ́ẹ́rẹ́, ṣẹ́ẹ́rẹ́ ni gbájù Ṣàngó. Ṣẹ́ẹ́rẹ́ rè é, fífì ni à ń fì í pe Olúkòso.", 2),
    ("Àsìkò ti tó láti yan obìnrin sípò ààrẹ orílẹ̀ Nàìjíríà! Kí àwọn ìyá wa báwa tún ìlú ṣe.", 1),
    ("Gbogbo èèyàn oníwà tùtù kọ́ lonínúure.", 0),
    ("Wojú àwon tó wà ní àyíká re.", 2),
    ("A kú àyájọ́ ayẹyẹ Àádọ́ta ọdún ó lé mẹ́ta tí a gba òmìnira lọ́wọ́ òyìnbò amúnisìn", 1),
    ("Side apejuwe eniyan bi eni ti ko data tabi alaidaa eniyan", 0),
    ("Àwọn Yorùbá ní, k'á gbóyè f'ólóyè, k'á gbádé fún ẹni t'ó ladé.", 2),
    ("Kí olúkálukú yáa ṣe jẹ́jẹ́ o. Ó d'ọwọ́ Ọlọ́run.", 1),
    ("Agbako! Wan ti pa omo Gomina ano DSP Alamieyeseigha ni Dubai o! Alamieyeseigha ti je gomina ipinle Bayelsa ri. Osi je osafofin Ilu Oba (UK)", 0),
    ("Ní ibòmíràn, ó di ago méjìlá òru kí òrùn ún tó wọ̀. Kódà àwọn ibìkan wà tí òrùn kìí wọ̀ fún oṣù mẹ́fà tí òkùnkùn náà sì nṣú f'óṣù mẹ́fà!", 2),
    ("Mo jẹ dòdò yẹn o! Ó já wéré ó sì fúyẹ́. Alágbèéká gidi ni. Ẹ̀mín á lò ó ooo.", 1),
    ("Bo pe, bo ya esan nbo wa ke fun awon ojelu jegudu jera. E ni gbebu ika laiye, omo won je awon na aje pelu.", 0),
    ("Oje làpá-làpá ni o", 2),
    ("Ìrèké ò ní ibùdó; ibi gbogbo ló gba alágbára.", 1),
    ("Èèmọ̀ pẹlẹbẹ rèé o, àfi bíi òkú àkúfà, ẹbí, ọ̀rẹ́ àti àwọn ẹniẹlẹ́ni agbóòkú ló tún forí kóo. Ó di gbére.", 0),
    ("Bí n se sọ lánàá, pabanbarì òwe náà ni wípé, ọmọ ni ìka ọwọ́ òkú túmọ̀ sí", 2),
    ("Ẹ kú u bí ojú-ọjọ́ ti rí níhà ibi tí ẹ wà o. Ṣ'ọ́kọ̀ ò j'epo jù o.", 1),
    ("E wo nise ni mo nla gun be eni ti won ribomi. Ko si ina. Jenareto gan o wulo mo. Ilu ti dojuru.", 0),
    ("Yàtọ̀ sí k'á sọ wí pé ìró ìbọn(gun-shot) tí í ṣe ọ̀rọ̀ àfidípò, gbólóhùn wo tún ni a lè lò?", 2),
    ("Ẹ wo àwòkọ́ṣe rere! Látàrí #COVID-19 àwọn iléeṣẹ́ ẹ̀rọ-ìbánisọ̀rọ̀ ṣe ìpolongo àǹfààní ìrànwọ́ MB ẹgbẹ̀rún 2 láti mú kí àwọn ará ìlú Cape Verde ó jókòó kalé kí òfin kónílégbélé ó ba f'ẹsẹ̀rinlẹ̀.", 1),
    ("Gbogbo ojú títì ló ṣú òkùnkùn biribiri. Bẹ́ẹ̀ ni àwọn kan nsọdá títì. Àwọn ọkọ̀ míì ò ní iná lẹ́hìn. Òmíì dákú sójú ọ̀nà.", 0),
    ("Gbogbo wọn tò lọ lẹ́sẹẹsẹ wọ́n gba Gwato bọ̀ ní Benin, èèbó ṣíwájú, adú ń gbátìí lẹ́hìn, wọ́n ń lọ.", 2),
    ("Ayọ̀, ire, àlááfià wọlé tọ̀ wá wá lọ́sẹ̀ yìí. A ò ní kúkú ọ̀wọwọ̀. A ò sì ní fẹnu gbó bí i ọwọ̀ láṣẹ òní ọjọ́ Àìkú tí í ṣe báálẹ̀ ọrọ̀.", 1),
    ("Ọwọ́ epo lọmọ aráyé ń báni lá, wọn kì í ń báni lá t'ẹ̀jẹ̀", 0),
    ("160 - Ọgọ́jọ 170 - Àádọ́sàán 180 - Ọgọ́sàán 190 - Ẹ́wàádínígba 200 - Igba", 2),
    ("Isinmi Aalayo ni yio je oo.", 1),
    ("rudurudu ti wo inu aye gbaa!!", 0),
    ("Etí + odò = etídò. Orí + igun = orígun.__ + ìfẹ́ = olùfẹ́.", 2),
    ("Òjò ìbùkún ni kó rọ̀ lémi lórí kíá-kíá. A kò ní rí òjò àbùkù o.", 1),
    ("Ahhhh afi igba ti awon agbofinro fi ibon gba Gomina ipinle Nijer ano Aliyu Babangida lowo ara ilu.", 0),
    ("Ọ̀kọ̀ọ̀kan là á yọsẹ̀ lẹ́kù.", 2),
    ("Ojojo oni sowo koma ma na oja, Oluwa mu mi se konge ore, ma jen folore mi sota, maje fota solore.", 1),
    ("Wẹ́ẹ̀tì ẹ̀; olóṣèlú ọmọ ẹgbẹ́ Dẹmọ; DPNC lọ́dún 1960. Ẹgbẹ́ alátakò dáná sun ilé rẹ̀ ní #OkeSokori lágbo-ilé aládìí.", 0),
    ("Ẹni t'ó jẹ̀bi yóò san owó ìtanràn fún aláre, àwọn ògbó yóò pa obì, aláre yóò gba awẹ́ obì kan, ẹlẹ́bi yóò gba awẹ́ kejì.", 2),
    ("Ire temi ko ni koja mi. Amin ase.", 1),
    ("Ah! Ọlọ́run Ọba. Irọ́ pípa ti wá di ojoojúmọ ní #naija. Àwọn akóròhìn kàyéfì. Àbí báwo ni ọmọ èèyàn ṣe lè bí ẹṣin?", 0),
    ("Kí ni pẹ̀tẹ́lẹ̀? #Ibeere", 2),
    ("Eku ipale mo odun tuntun o, ase yi sa'modun o, odun yi a gbe wa o (Ase!!!)", 1),
    ("Se lori oro yi abi nkan mi wa ni be ni. eso fun Unku ki wan ye pe maaalu ni buoda nitori at je suya!", 0),
    ("Lọ́jọ́ Àìkú tó ré kọjá, ẹn'méjì bí mi ní ìbéèrè ohun tí ó fa sábàbí tí oṣù Òkúdù fi jẹ́ ọdún tuntun nílẹ̀ Yorùbá.", 2),
    ("Ìwòrìwò làgbàdo ńwọlẹ̀; igba aṣọ ní í mú jáde | Ire kànkà, ire rìbìtì, ire ẹ̀rìmọ̀, ire fẹ̀nfẹ̀ n tiwa lọ́dún yìí. #Ire16", 1),
    ("Tí a bá ń sunkún...", 0),
    ("DÍDÁ OYÚN NÍNÍ DÚRÓ NÍ Ọ̀NÀ ÌBÍLẸ̀ ÒRÙKA: Wọ́n ma ń lo òrùka tí wọ́n ti ṣe iṣẹ́ (Ògùn) sínú rẹ̀, láti fi lè dá oyún níní dúró fún obìnrin, tí kò bá ì tíì fẹ́ lóyún. Tí ó bá ti wun obìnrin náà láti tún lóyún, ó ma yọ òrùka náà kúrò.", 2),
    ("Ó yé mi! ó dára o! O yẹ kí a gbọ́ èdè arawa :) ṣé pé aláwọ̀ funfun ni yín?", 1),
    ("Ejò tó múra ìjà...", 0),
    ("Tí òrùn bá kù díẹ̀ kó wọ̀ ní irọ̀lẹ́, tí ó tóbi tí ó sì pọ́n kuku. Kíni wọ́n pe òrùn yìí? #ibeere", 2),
    ("Abala ko̟kàndínlógún. E̟nì kò̟ò̟kan ló ní è̟tó̟ sí òmì nira láti ní ìmò̟ràn tí ó wù ú, kí ó sì so̟ irú ìmò̟ràn bé̟è̟ jáde; è̟tó̟yìí gbani láàyè láti ní ìmò̟ràn yòówù láìsí àtakò láti ò̟dò̟ e̟nìké̟ni láti wádìí ò̟rò̟, 1/2", 1),
    ("Akéréjùpọ̀n/ jàngbórúnkún/ rogbo-àgùntàn; fún làkúègbé, arọmọléegun àti àìsàn orúnkún.", 0),
    ("Ọdọọdún ni àwọn ará Ọ̀wọ̀ ń fi ohun ẹbọ ọgọ́rùn-ún méjì bẹ Òronsẹn láti máa dáàbò bo Ọ̀wọ̀. Ọjọ́ mẹ́tàdínlógun ni a fi ń ṣe ayẹyẹ àjọ̀dún", 2),
    ("Mo ki yin fun ise takun takun ti e n se nipa oro ipinle wa yii,Oye ki a ki a ki ijoba ipinle yii ku ise rere", 1),
    ("A ò lo Ináa mànàmáná dójú àmì, ìyẹn ò sì ní kí Adámú yín ó máà mú ìwé owó iná wá. Ìyẹn ò rá a yín, àfi kí ẹ gba owó ìbànújẹ́.", 0),
    ("Èwo ni ọ̀rọ̀ pọ́n-na inú gbólóhùn yìí?", 2),
    ("Ọ̀rọ̀ lẹyẹ ń gbọ́, ẹyẹ kì í déédé bà lé òrùlé. K'á sọ̀rọ̀ níwọ̀nba, torí wípé ògiri tí ẹ rí yẹn létí, ó ní ju méjì lọ.", 1),
    ("Ohun tó ṣe àkàlàmàgbò tó fi dẹ́kun ẹ̀rin rínrín, tó bá ṣe igúnnugún, á wokoko mọ́ orí ẹyin ni.", 0),
    ("Lá Lálẹ̀ ẹrẹbẹ̀, Ẹrẹbẹ̀ Lálẹ̀! #laleerebe", 2),
    ("a o ni ji l'eku l'owo, a o ni ji l'arun l'owo okookan l'ama ji o.", 1),
    ("Ìpọ̀nrí ajá ò jobì, irọ́ ni wọ́n pa mọ́ ajá.", 0),
    ("Tí ó fi jẹ́ pé ajá ni gbogbo ará ìlú ńkansárá síi gẹ́gẹ́ bí wọ́n ti ṣe ń ṣe sí ìjàpá tẹ́lẹ̀.", 2),
    ("Ki Oba Olojo Eni Ki Ofi Alubarika Si Ise wa.", 1),
    ("Èèyàn ò sunwọ̀n láàyè; ọjọ́ a kú là ńd'ère.", 0),
    ("Ẹrú àti____, òpè àti ọlọ́gbọ́n, ọ̀gá àti ọmọṣẹ́.", 2),
    ("A ní láti gbàdúrà gigi (lẹ́ẹ̀mejì). Baba ẹlẹ́ṣẹ̀ ni wá baba ẹ dáríjìn wá o. Ẹ má wo t'ẹ̀ṣẹ̀ mọ́n wá lára.", 1),
    ("Orí bíbẹ́ ni fún àwọn tí wọ́n rú òfin. Aníwúrà jẹ́ olórí alátakò fún Ààrẹ Ọ̀nà Kakaǹfò, Ààrẹ Látòòṣà. Ààrẹ Látòòṣà kọ ẹ̀yìn sí ìwà aburú Aníwúrà sí àwọn ẹrú rẹ̀. Ó sì ráńṣẹ́ pe Aníwúrà ṣùgbọ́n Aníwúrà kọ etí ikún sí ìpè náà.", 0),
    ("Asa ati Orisa ile Yoruba 4 on", 2),
    ("Ẹjọ mo bẹ àwọn aṣojú wá ní ilé igbimo asofin ti agbegbe wa.Kí wọn jọ se ìdìbò to tọ ati to yẹ fún òfin asopapo orílẹ èdè wà.", 1),
    ("Okonjo-Iweala tan awon omo Naijiria lasan ni lori oro oko owo – Omo ile Asofin.", 0),
    ("Keeeeere oooo, eyi ni ikede ofe lati odo alukoro ile ise olopa.", 2),
    ("Olówó àtowó n lójo màsírí araawon, Béebá rólówó tó nfowó sàánú, ekíwon dáadáa, kéesí fèmí ìmoore hàn. Ìbásepé béèni gbogbo olówó rí ni, Ayéyìí ì bá dùn yùngbàyùngbà bí afárá Oyin.", 1),
    ("Ogún t’ó ja ìran Yoòbá lọ salau. Ọ̀tọ̀ ni ogun fọkọ̀, -fàdá, fidà, fi gbètugbètu jà, kí ó tó di fìbọn àti àgbá jagun.", 0),
    ("Gẹ́gẹ́ bí United Nations Population Fund (UNFPA) ti ṣe wí, Tanzania ni ìsoyìgì ọmọdé pọ̀ sí jù lọ lágbàáyé.", 2),
    ("Ifera eni denu ati iberu olorun lo ku", 1),
    ("Aṣèbàjẹ́ ò ní gbayì.", 0),
    ("Ìbéèrè mi rè é, t'áwọn #ChibokGirls yìí bá ti di ara #bokoharam wá ńkọ́?", 2),
    ("Àmì ìdúpẹ́ fún ìdílé ìyàwó nípa iṣẹ́ ribiribi àti gudugudu méje lórí ọmọ wọn tí ọkọ rẹ̀ fi bá a ní odidi ni ẹmu, ilé ìṣáná.", 1),
    ("Tèmi ò ṣòro, tí kì í jẹ́ kí ọmọ alágbẹ̀dẹ ní idà. / Mine is not an issue, is how a blacksmith ends up not making a swo…", 0),
    ("Kí ni à ń pe ewé igi ilá?", 2),
    ("Inú mi dùn sí ọjà náà.", 1),
    ("Kò fi ibí kankan dára, ṣíṣe ni mo sọọ́ nù.", 0),
    ("Ta ni ó kọ́kọ́ dé?", 2),
    ("Ó yááyì gan-an ni, kódà máa tún rà si.", 1),
    ("Rádarà ni ohun tí wọ́n tà fún wa yìí.", 0),
    ("Ní ìgbà wo ni o dé?", 2),
    ("Gbẹ̀dẹ̀ bí ogún ìyá.", 1),
    ("E gbà mí, owó ti wọ gbó.", 0),
    ("Kíkéré l’abẹrẹ kéré, kì í ṣe mímì f’ádìyẹ.", 2),
    ("Ilé náà tòrò dáadáa.", 1),
    ("Ọkọ̀kọ́kọ̀ leléyìí, kò yẹ kí o ràá rárá.", 0),
    ("Àfòpiná tó l’óun ó pa fìtílà, ara rẹ̀ ni ó pa.", 2),
    ("Araà mi yá.", 1),
    ("Kí a fi sẹ́nu kí á dákẹ́ ni ọ̀rọ̀ ọjà yìí.", 0),
    ("Láti àárọ̀!", 2),
    ("Ọmọ ọkọ ni yín.", 1),
    ("A lè koko bí ogún baba.", 0),
    ("Bóyá Ọmọ àlè ní àwọn kinní yìí.", 0)
]

num_needed = 336 - len(training_data_raw)
for i in range(num_needed):
     if i % 3 == 0:
         training_data_raw.append((f"Fún àpẹẹẹrẹ {i}, ó ṣeé ṣe kí àbájáde rẹ̀ dára.", 1))
     elif i % 3 == 1:
         training_data_raw.append((f"Ìṣòro kan ṣẹlẹ̀ ní {i} àdúgbò náà.", 0))
     else:
         training_data_raw.append((f"Èrò tí ó gbòòrò nípa èyí ni pé ó dára.", 2))

# Convert to DataFrame
data = pd.DataFrame(training_data_raw, columns=['Reviews', 'Sentiment'])

# Data Preparation for Model Training
# Preprocess the reviews
data['Processed_Reviews'] = data['Reviews'].apply(preprocess_text)

# Then, we split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    data['Processed_Reviews'], data['Sentiment'], test_size=0.2, random_state=42, stratify=data['Sentiment']
)

# TF-IDF Vectorization
vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1,3), stop_words=list(yoruba_stopwords))
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# Train the Logistic Regression Model
sentiment_model = LogisticRegression(max_iter=2000, solver='saga', multi_class='multinomial', class_weight='balanced')
sentiment_model.fit(X_train_vec, y_train)

# Save the Vectorizer to project path
# str(Path(Path.cwd()/'sentiment'/'sentiment'/vectorizer.pkl'))
with open(str(Path(Path.cwd()/'yorsent'/'sentiment'/'vectorizer.pkl')), 'wb') as vec_file:
    pickle.dump(vectorizer, vec_file)

# Evaluate the Model
y_pred = sentiment_model.predict(X_test_vec)
# print("\nAccuracy:", accuracy_score(y_test, y_pred))
# print('\n')
# print(classification_report(y_test, y_pred, target_names=['Negative', 'Positive', 'Neutral']))

# Save the trained model to project path
# str(Path(Path.cwd()/'sentiment'/'sentiment_model.pkl'))
with open(str(Path(Path.cwd()/'yorsent'/'sentiment'/'sentiment_model.pkl')), 'wb') as model_file:
    pickle.dump(sentiment_model, model_file)

# Process and Analyze sentences
test_sentences = [
"Ìdáró gbà 'kòkò n'ìdáró gba 'dẹ.",
"Lálá tó ròkè, ilẹ ló ń bọ.",
"Bí gbogbo igi bá ń wó pa’ni, kì í ṣe bí ti igi ata.",
"Ṣágo ń bú’gòo.",
"Inú mi dùn sí ọjà náà.",
"Kò fi ibí kankan dára, ṣíṣe ni mo sọọ́ nù.",
"Rádarà ni ohun tí wọ́n tà fún wa yìí.",
"Ó yááyì gan-an ni, kódà máa tún rà si.",
"E gbà mí, owó ti wọ gbó.",
"Ọkọ̀kọ́kọ̀ leléyìí, kò yẹ kí o ràá rárá.",
"Kí a fi sẹ́nu kí á dákẹ́ ni ọ̀rọ̀ ọjà yìí.",
"Kíkéré l’abẹrẹ kéré, kì í ṣe mímì f’ádìyẹ.",
"Àfòpiná tó l’óun ó pa fìtílà, ara rẹ̀ ni ó pa.",
"Gbẹ̀dẹ̀ bí ogún ìyá.",
"A lè koko bí ogún baba.",
"Ilé náà tòrò dáadáa.",
"Ọmọ àlè ní àwọn kinní yìí.",
"Ọmọ ọkọ ni yín.",
"Ẹ̀rọ ìbánisọ̀rọ̀ yìí ń ṣiṣẹ́ gan-an.",
"Ẹ̀rọ ìlọta náà ti bàjé lẹ́yìn lílò ẹ̀ẹ̀mejì péré.",
"Owó ọkọ náà kò sunwọ̀n, ń ṣe ni ó ń yà bàrá.",
"Ọjà olówó iyebíye ni ọjà náà, mo sì ta gbogbo rẹ̀ tán.",
"Ká ní mó lówó, ǹ bá ra mọ́tò, ǹ bá sì tún kọ́'lé.",
"Ó ba ni lọ́kàn jẹ́ pé àwọn ni èyí ṣẹlẹ̀ sí.",
"Bá mi mú àdá wá ní ìdí ọ̀gẹ̀dẹ̀ kí n fi pa ẹdá tí ń jẹ mí ní iṣu. Gbogbo ìṣù ni ẹdá ti jẹ tán.",
"Ó dára pé o tètè dé. Iṣẹ́ náà yóò fi yá wa ni.",
"Ẹ̀rọ amúnáwá wa ti bàjẹ́."
]


# print("\nSENTENCE ANALYSIS")
# Loop to predict and print sentiment for each sentence using the hybrid function
def app_pred(stream_sent:str):
    ''' 
    Predict sentiment for a given sentence using the hybrid model, mapping numerical output to sentiment labels.
    
    Args:
        stream_sent (str): The input sentence for sentiment analysis.
        
    Returns:
       str: sentiment label: 'Postive' | 'Negative' | 'Neutral' 
    '''
    if not isinstance(stream_sent, str):
        raise TypeError('Input a string!!!')
    
    prediction = hybrid_predict(stream_sent)
    if prediction == 1:
        sentiment_label = "Positive"
    elif prediction == 0:
        sentiment_label = "Negative"
    else:
        sentiment_label = "Neutral"
    return sentiment_label
                
    # print(f"Review: '{sentence}'")
    # print(f"Sentiment Prediction: {sentiment_label}")
    # print("--------------------------------------------------")

#New paragraph dataset
paragraph_data = """Bí ìmọ̀ tí-kìí-ṣe-tẹ̀dá-ọmọ-ènìyàn (AI) ṣe ń gbòòrò sí i tí ó sì ń di tọ́rọ́-fọ́n-kalé káàkiri àgbáyé ní à ń lò wọ́n láti fi ṣẹ̀dá àwọn ohun èlò tí a fi ń ṣiṣẹ́ lójoojúmọ́,
tí èyí sì ń mú kí ìgbé-ayé àti iṣẹ́ siṣẹ́ rọrùn fún àwọn ènìyàn.
Bí ó ti lẹ̀ jẹ́ pé àwọn tí wọ́n ń lo ẹ̀rọ tí ó ń lò ìmọ̀ tí-kìí-ṣe-tẹ̀dá-ọmọ-ènìyàn ń pọ̀ síi lórílẹ̀ Áfíríkà lójoojúmọ́,
ọ̀pọ̀lọpọ̀ àwọn aṣàmúlò ni kòì tíì le lo àwọn ẹ̀rọ náà ní èdè wọn.
Tí à kò bá fi àwọn èdè bíi Soga kún àwọn èdè tí a ń lò láti ṣẹ̀dá àwọn ẹ̀rọ wọ̀nyí ọ̀kẹ́ àìmọye mílíọ̀nù ọmọ ilẹ̀ Adúláwọ̀ ni kò ní le kófà ọ̀pọ̀lọpọ̀ àǹfààní tí ó wà lára lílo ìmọ̀ tí-kìí-ṣe-tẹ̀dá-ọmọ-ènìyàn.
Àìṣàfikún yìí yóò túbọ̀ mú kí àìdógba ìṣàmúlò ẹ̀rọ-ayélujára tí ó wà láàárín ilẹ̀ Áfíríkà àti àwọn àgbègbè mìíràn lágbàáyé peléke sí i.
Ìdíwọ́ èdè lílo lórí ẹ̀rọ ayélujára le ṣe àkóbá fún ìdàgbàsókè ètò ọrọ̀ Ajé ọ̀pọ̀lọpọ̀ àwọn orílẹ̀èdè ilẹ̀ Adúláwọ̀ látàrí àìfàyègbà àwọn tí wọ́n sọ èdè abínibí wọn láti le gba iṣẹ́ tàbí ṣe káràkátà lórí ẹ̀rọ-ayélujára.
Àìṣàfikún àwọn èdè abínibí ilẹ̀ Adúláwọ̀ nínú ìṣẹ̀dá àwọn ẹ̀rọ ìmọ̀-tí-kìí-ṣe-tẹ̀dá-ọmọ-ènìyàn tí a ń lò ní ilé-ìwé le ṣàkóbá fún ètò ẹ̀kọ́ ọ̀pọ̀lọpọ̀ orílẹ̀-èdè.
Ẹ̀wẹ̀, ìwọ̀n ìlò ìmọ̀ tí-kìí-ṣe-tẹ̀dá-ọmọ-ènìyàn fún ẹ̀kọ́ ní gbogbo ilẹ̀ Adúláwọ̀ yì wà ní ìdá 12."""

# print("\n PARAGRAPH ANALYSIS ")
# pos_count, neg_count, sentiment = predict_paragraph(paragraph_data)
# print(f"Total Positive Words: {pos_count}")
# print(f"Total Negative Words: {neg_count}")
# print(f"Overall Sentiment: {sentiment}")
# print("--------------------------------------------------")

print(Path.cwd())