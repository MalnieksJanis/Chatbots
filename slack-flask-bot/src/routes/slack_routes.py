from flask import Blueprint, request, make_response, jsonify
from slack_sdk.signature import SignatureVerifier
from Src.Config import SLACK_SIGNING_SECRET, SLACK_BOT_TOKEN
from Src.Bot import SlackBot
from Utils.Helpers import load_json, save_json
import json
from datetime import datetime
import random

bp = Blueprint('slack', __name__)
verifier = SignatureVerifier(SLACK_SIGNING_SECRET)
bot = SlackBot(SLACK_BOT_TOKEN)

# Vienkārša lietotāju datu bāze (JSON fails)
USERS_FILE = "data/users.json"
MEDIJUMI_FILE = "data/medijumi.json"

# Lietotāju sesiju glabāšanai (vienkārši atmiņā, produkcijā izmantot DB)
user_sessions = {}

# Limitēti medību sezonas dati
LIMITED_HUNTING_SEASONS = {
    # Limitēti medījamie dzīvnieki
    "alnis": [("01.09.", "31.12.")],
    "staltbriedis_bulls": [("01.09.", "15.02.")],
    "staltbriedis_bulls_jaunie": [("15.08.", "31.03.")],
    "staltbriedis_govis": [("15.07.", "31.01.")],
    "staltbriedis_teli": [("15.07.", "31.03.")],
    "vilks": [("15.07.", "31.03.")],
    # Limitētie putni
    "mednis": [("01.09.", "31.12.")],
    "rubeņi": [("01.09.", "31.12.")],
    "rakelis": [("01.09.", "31.12.")],
    "mežirbe": [("01.09.", "31.01.")],
}

# Nelimitēti medību sezonas dati
UNLIMITED_HUNTING_SEASONS = {
    # Nelimitēti medījamie dzīvnieki
    "mežacūka": [("01.01.", "31.12.")],
    "stirna_azis": [("01.06.", "30.11.")],
    "stirna_kazleni_kazas": [("15.08.", "30.11.")],
    "bebrs": [("15.07.", "15.04.")],
    "ondatra": [("15.07.", "15.04.")],
    "ondatra_melioracija": [("15.07.", "30.04.")],
    "pelēkais_zaķis": [("01.10.", "31.01.")],
    "baltais_zaķis": [("01.10.", "31.01.")],
    "meža_cauna": [("01.10.", "31.03.")],
    "akmens_cauna": [("01.10.", "31.03.")],
    "sesks": [("01.10.", "31.03.")],
    "āpsis": [("01.08.", "31.03.")],
    "lapsa": [("01.01.", "31.12.")],
    "jenotsuns": [("01.01.", "31.12.")],
    "amerikas_udele": [("01.01.", "31.12.")],
    "dambrieži": [("01.01.", "31.12.")],
    "mufloni": [("01.01.", "31.12.")],
    "sika_briedis": [("01.01.", "31.12.")],
    "jenots": [("01.01.", "31.12.")],
    "nutrija": [("01.01.", "31.12.")],
    "baibaks": [("01.01.", "31.12.")],
    "šakālis": [("01.01.", "31.12.")],
    # Nelimitētie putni
    "fazāns": [("01.08.", "31.03.")],
    "lauku_balozis": [("01.08.", "15.11.")],
    "majas_balozis": [("01.08.", "31.12.")],
    "sloka": [("01.09.", "15.12.")],
    "pelēkā_vārna": [("15.06.", "30.04.")],
    "žagata": [("15.06.", "30.04.")],
    "sejas_zoss": [("15.09.", "30.11.")],
    "baltpieres_zoss": [("15.09.", "30.11.")],
    "kanādas_zoss": [("15.09.", "30.11.")],
    "mežazosis": [("15.09.", "30.11.")],
    "garkaklis": [("15.09.", "30.11.")],
    "platknābis": [("15.09.", "30.11.")],
    "baltvēderis": [("15.09.", "30.11.")],
    "meža_zoss": [("15.09.", "30.11.")],
    "lauči": [("15.09.", "30.11.")],
    "krīkļi": [("15.09.", "30.11.")],
    "pelēkā_pīle": [("15.09.", "30.11.")],
    "meža_pīle": [("15.09.", "30.11.")],
    "prīkšķe": [("15.09.", "30.11.")],
    "cekulpīle": [("15.09.", "30.11.")],
    "kerra": [("15.09.", "30.11.")],
    "melnā_pīle": [("15.09.", "30.11.")],
    "gaigala": [("15.09.", "30.11.")],
    "pīle": [("20.08.", "14.09."), ("15.09.", "15.12.")],
}

# Apvienotie medību sezonas dati
HUNTING_SEASONS = {**LIMITED_HUNTING_SEASONS, **UNLIMITED_HUNTING_SEASONS}

ANIMAL_FACTS = {
    "alnis": [
        "Alnis ir lielākais briežu dzimtas pārstāvis Eiropā.",
        "Alnim ir ļoti laba peldētprasme – tas var peldēt pat vairākus kilometrus.",
        "Alņa ragi var sasniegt līdz pat 2 metru platumu."
    ],
    "staltbriedis": [
        "Staltbrieža ragi katru gadu pilnībā nomainās.",
        "Staltbrieži ir vieni no skaļākajiem dzīvniekiem riesta laikā.",
        "Staltbrieži var sasniegt ātrumu līdz 65 km/h."
    ],
    "mežacūka": [
        "Mežacūkas ir ļoti inteliģenti un sabiedriski dzīvnieki.",
        "Mežacūkas var izrakt zemi līdz pat 15 cm dziļumā, meklējot barību.",
        "Mežacūkas ir izplatītas gandrīz visā Eiropā."
    ],
    "bebrs": [
        "Bebri ir lielākie grauzēji Eiropā.",
        "Bebri būvē dambjus, lai aizsargātu savas mājas no plēsējiem.",
        "Bebra zobi aug visu mūžu un ir oranži, jo satur dzelzi."
    ],
    "vilks": [
        "Vilki dzīvo baros un sadarbojas medībās.",
        "Vilka gaudošana palīdz sazināties ar citiem bara locekļiem.",
        "Vilki var nostaigāt līdz pat 50 km dienā."
    ],
    "zaķis": [
        "Zaķiem ir ļoti laba dzirde un redze.",
        "Zaķis var lekt līdz pat 3 metru tālumā.",
        "Zaķa ausis palīdz regulēt ķermeņa temperatūru."
    ],
    "mednis": [
        "Mednis ir lielākais Latvijas meža putns.",
        "Medņa tēviņš pavasarī dzied īpašu dziesmu – 'tokšanu'.",
        "Medņi dzīvo vecos skujkoku mežos."
    ],
    "rubeņi": [
        "Rubeņi ir ļoti piesardzīgi putni.",
        "Rubeņu tēviņi pavasarī pulcējas riestā.",
        "Rubeņi barojas galvenokārt ar pumpuriem un ogām."
    ],
    "mežirbe": [
        "Mežirbes ir ļoti labi maskētas savā vidē.",
        "Mežirbes ligzdo uz zemes, bieži zem krūmiem.",
        "Mežirbes ziemā barojas ar koku pumpuriem."
    ],
    "fazāns": [
        "Fazāni ir krāšņi putni, īpaši tēviņi.",
        "Fazāni sākotnēji ievesti Latvijā no Āzijas.",
        "Fazāni skrien ātrāk nekā lido."
    ],
    "zoss": [
        "Zosis veido V veida kāšus migrācijas laikā.",
        "Zosis ir ļoti uzticīgas savai ģimenei.",
        "Zosis var lidot tūkstošiem kilometru garās migrācijās."
    ],
    "pīle": [
        "Pīles spēj ienirt līdz pat 2 metru dziļumā.",
        "Pīļu tēviņi pavasarī ir ļoti krāšņi.",
        "Pīles bieži maina spalvas vasaras beigās."
    ]
}

def is_in_season(animal, today=None):
    if today is None:
        today = datetime.now()
    if animal not in HUNTING_SEASONS:
        return None
    for start, end in HUNTING_SEASONS[animal]:
        start_dt = datetime.strptime(f"{start}{today.year}", "%d.%m.%Y")
        end_dt = datetime.strptime(f"{end}{today.year}", "%d.%m.%Y")
        # Ja sezona pāriet pāri gadam
        if end_dt < start_dt:
            end_dt = end_dt.replace(year=end_dt.year + 1)
        if start_dt <= today <= end_dt:
            return True
    return False

def get_user_data():
    try:
        return load_json(USERS_FILE)
    except Exception:
        return {}

def save_user_data(data):
    save_json(USERS_FILE, data)

@bp.route('/slack/events', methods=['POST'])
def slack_events():
    if not verifier.is_valid_request(request.get_data(), request.headers):
        return make_response("Invalid request signature", 403)

    event_data = request.json

    # Slack URL verification
    if 'challenge' in event_data:
        return make_response(event_data['challenge'], 200, {"content_type": "application/json"})

    # Tikai parastu ziņu apstrāde (bez bot ID)
    if 'event' in event_data and event_data['event']['type'] == 'message' and 'bot_id' not in event_data['event']:
        user = event_data['event']['user']
        text = event_data['event']['text'].strip().lower()
        channel = event_data['event']['channel']

        # Ja lietotājs ievada apliecības numuru
        if user in user_sessions and user_sessions[user].get("awaiting") == "license":
            license_number = text
            users = get_user_data()
            if license_number not in users:
                users[license_number] = {"medijumi": []}
            user_sessions[user]["license"] = license_number
            user_sessions[user]["awaiting"] = None
            save_user_data(users)
            bot.send_message(channel, "Apliecības numurs saglabāts. Ko vēlies darīt tālāk?", blocks=[
                {
                    "type": "actions",
                    "elements": [
                        {"type": "button", "text": {"type": "plain_text", "text": "Pievienot medījumu"}, "value": "add_medijums", "action_id": "add_medijums"},
                        {"type": "button", "text": {"type": "plain_text", "text": "Apskatīt savus medījumus"}, "value": "view_medijumi", "action_id": "view_medijumi"},
                        {"type": "button", "text": {"type": "plain_text", "text": "Atgriezties sākumā"}, "value": "sākums", "action_id": "sākums"}
                    ]
                }
            ])
            return make_response("", 200)

        # Ja lietotājs ievada medījuma nosaukumu
        if user in user_sessions and user_sessions[user].get("awaiting") == "medijums":
            medijums = text
            license_number = user_sessions[user]["license"]
            users = get_user_data()
            if license_number in users:
                users[license_number]["medijumi"].append({
                    "nosaukums": medijums,
                    "datums": datetime.now().strftime("%Y-%m-%d")
                })
                save_user_data(users)
                bot.send_message(channel, f"Medījums '{medijums}' pievienots!")
            user_sessions[user]["awaiting"] = None
            bot.send_message(channel, "Vai vēlies vēl ko darīt?", blocks=[
                {
                    "type": "actions",
                    "elements": [
                        {"type": "button", "text": {"type": "plain_text", "text": "Atgriezties sākumā"}, "value": "sākums", "action_id": "sākums"},
                        {"type": "button", "text": {"type": "plain_text", "text": "Beigt sarunu"}, "value": "beigt", "action_id": "beigt"}
                    ]
                }
            ])
            return make_response("", 200)

        if text == "sākums":
            bot.send_message(channel, "Sveicināts Medību Palīgā! Ko vēlies darīt?", blocks=[
                {
                    "type": "actions",
                    "elements": [
                        {"type": "button", "text": {"type": "plain_text", "text": "Pievienot iesniegumu"}, "value": "add_report", "action_id": "add_report"},
                        {"type": "button", "text": {"type": "plain_text", "text": "Dzīvnieks vai putns"}, "value": "animal_fact", "action_id": "animal_fact"},
                        {"type": "button", "text": {"type": "plain_text", "text": "Medību sezona"}, "value": "hunting_season", "action_id": "hunting_season"}
                    ]
                }
            ])

    return make_response("", 200)

@bp.route('/slack/interactions', methods=['POST'])
def slack_interactions():
    if not verifier.is_valid_request(request.get_data(), request.headers):
        return make_response("Invalid request signature", 403)

    payload = request.form.get('payload')
    if payload:
        interaction = json.loads(payload)
        user_id = interaction['user']['id']
        channel_id = interaction['channel']['id']

        # Pogu klikšķu apstrāde
        if interaction['type'] == 'block_actions':
            action = interaction['actions'][0]
            action_id = action['action_id']

            if action_id == "add_report":
                user_sessions[user_id] = {"awaiting": "license"}
                bot.send_message(channel_id, "Lūdzu ievadi mednieka apliecības numuru:")

            elif action_id == "add_medijums":
                user_sessions[user_id]["awaiting"] = "medijums"
                bot.send_message(channel_id, "Ievadi nomedītā dzīvnieka vai putna nosaukumu:")

            elif action_id == "view_medijumi":
                license_number = user_sessions[user_id].get("license")
                users = get_user_data()
                if license_number and license_number in users and users[license_number]["medijumi"]:
                    medijumi = users[license_number]["medijumi"]
                    msg = "Tavi medījumi:\n" + "\n".join([f"{m['nosaukums']} ({m['datums']})" for m in medijumi])
                else:
                    msg = "Nav neviena reģistrēta medījuma."
                bot.send_message(channel_id, msg)

            elif action_id == "sākums":
                bot.send_message(channel_id, "Sveicināts Medību Palīgā! Ko vēlies darīt?", blocks=[
                    {
                        "type": "actions",
                        "elements": [
                            {"type": "button", "text": {"type": "plain_text", "text": "Pievienot iesniegumu"}, "value": "add_report", "action_id": "add_report"},
                            {"type": "button", "text": {"type": "plain_text", "text": "Dzīvnieks vai putns"}, "value": "animal_fact", "action_id": "animal_fact"},
                            {"type": "button", "text": {"type": "plain_text", "text": "Medību sezona"}, "value": "hunting_season", "action_id": "hunting_season"}
                        ]
                    }
                ])

            elif action_id == "beigt":
                bot.send_message(channel_id, "Paldies par sarunu! Lai veicas medībās!")

            # Pievieno loģiku katram konkrētajam dzīvniekam vai putnam, lai atdotu random faktus
            elif action_id == "animal_fact":
                bot.send_message(channel_id, "Izvēlies dzīvnieku vai putnu:", blocks=[
                    {
                        "type": "actions",
                        "elements": [
                            {"type": "button", "text": {"type": "plain_text", "text": "Dzīvnieks"}, "value": "fact_animal", "action_id": "fact_animal"},
                            {"type": "button", "text": {"type": "plain_text", "text": "Putns"}, "value": "fact_bird", "action_id": "fact_bird"}
                        ]
                    }
                ])
            elif action_id == "fact_animal":
                animals = ["alnis", "staltbriedis", "mežacūka", "bebrs", "vilks", "zaķis"]
                bot.send_message(channel_id, "Izvēlies dzīvnieku:", blocks=[
                    {
                        "type": "actions",
                        "elements": [
                            {"type": "button", "text": {"type": "plain_text", "text": a.capitalize()}, "value": f"fact_{a}", "action_id": f"fact_{a}"} for a in animals
                        ]
                    }
                ])
            elif action_id == "fact_bird":
                birds = ["mednis", "rubeņi", "mežirbe", "fazāns", "zoss", "pīle"]
                bot.send_message(channel_id, "Izvēlies putnu:", blocks=[
                    {
                        "type": "actions",
                        "elements": [
                            {"type": "button", "text": {"type": "plain_text", "text": b.capitalize()}, "value": f"fact_{b}", "action_id": f"fact_{b}"} for b in birds
                        ]
                    }
                ])
            elif action_id.startswith("fact_"):
                animal = action_id.replace("fact_", "")
                facts = ANIMAL_FACTS.get(animal)
                if facts:
                    fact = random.choice(facts)
                    bot.send_message(channel_id, f"Fakts par {animal}: {fact}")
                else:
                    bot.send_message(channel_id, "Par šo dzīvnieku/putnu fakts nav pieejams.")

            elif action_id == "hunting_season":
                bot.send_message(channel_id, "Izvēlies dzīvnieku vai putnu un tipu:", blocks=[
                    {
                        "type": "actions",
                        "elements": [
                            {"type": "button", "text": {"type": "plain_text", "text": "Limitētie dzīvnieki"}, "value": "season_limited_animal", "action_id": "season_limited_animal"},
                            {"type": "button", "text": {"type": "plain_text", "text": "Nelimitētie dzīvnieki"}, "value": "season_unlimited_animal", "action_id": "season_unlimited_animal"},
                            {"type": "button", "text": {"type": "plain_text", "text": "Limitētie putni"}, "value": "season_limited_bird", "action_id": "season_limited_bird"},
                            {"type": "button", "text": {"type": "plain_text", "text": "Nelimitētie putni"}, "value": "season_unlimited_bird", "action_id": "season_unlimited_bird"},
                        ]
                    }
                ])
            elif action_id == "season_limited_animal":
                animals = [k for k in LIMITED_HUNTING_SEASONS.keys() if k not in ["mednis", "rubeņi", "rakelis", "mežirbe"]]
                bot.send_message(channel_id, "Izvēlies limitēto dzīvnieku:", blocks=[
                    {
                        "type": "actions",
                        "elements": [
                            {"type": "button", "text": {"type": "plain_text", "text": a.replace('_', ' ').capitalize()}, "value": f"season_{a}", "action_id": f"season_{a}"} for a in animals
                        ]
                    }
                ])
            elif action_id == "season_unlimited_animal":
                animals = [k for k in UNLIMITED_HUNTING_SEASONS.keys() if k not in [
                    "fazāns", "lauku_balozis", "majas_balozis", "sloka", "pelēkā_vārna", "žagata", "sejas_zoss", "baltpieres_zoss", "kanādas_zoss", "mežazosis", "garkaklis", "platknābis", "baltvēderis", "meža_zoss", "lauči", "krīkļi", "pelēkā_pīle", "meža_pīle", "prīkšķe", "cekulpīle", "kerra", "melnā_pīle", "gaigala", "pīle"
                ]]
                bot.send_message(channel_id, "Izvēlies nelimitēto dzīvnieku:", blocks=[
                    {
                        "type": "actions",
                        "elements": [
                            {"type": "button", "text": {"type": "plain_text", "text": a.replace('_', ' ').capitalize()}, "value": f"season_{a}", "action_id": f"season_{a}"} for a in animals
                        ]
                    }
                ])
            elif action_id == "season_limited_bird":
                birds = [k for k in LIMITED_HUNTING_SEASONS.keys() if k in ["mednis", "rubeņi", "rakelis", "mežirbe"]]
                bot.send_message(channel_id, "Izvēlies limitēto putnu:", blocks=[
                    {
                        "type": "actions",
                        "elements": [
                            {"type": "button", "text": {"type": "plain_text", "text": b.replace('_', ' ').capitalize()}, "value": f"season_{b}", "action_id": f"season_{b}"} for b in birds
                        ]
                    }
                ])
            elif action_id == "season_unlimited_bird":
                birds = [k for k in UNLIMITED_HUNTING_SEASONS.keys() if k in [
                    "fazāns", "lauku_balozis", "majas_balozis", "sloka", "pelēkā_vārna", "žagata", "sejas_zoss", "baltpieres_zoss", "kanādas_zoss", "mežazosis", "garkaklis", "platknābis", "baltvēderis", "meža_zoss", "lauči", "krīkļi", "pelēkā_pīle", "meža_pīle", "prīkšķe", "cekulpīle", "kerra", "melnā_pīle", "gaigala", "pīle"
                ]]
                bot.send_message(channel_id, "Izvēlies nelimitēto putnu:", blocks=[
                    {
                        "type": "actions",
                        "elements": [
                            {"type": "button", "text": {"type": "plain_text", "text": b.replace('_', ' ').capitalize()}, "value": f"season_{b}", "action_id": f"season_{b}"} for b in birds
                        ]
                    }
                ])
            elif action_id.startswith("season_"):
                animal = action_id.replace("season_", "")
                # Meklē sezonu abās vārdnīcās
                season = LIMITED_HUNTING_SEASONS.get(animal) or UNLIMITED_HUNTING_SEASONS.get(animal)
                if season:
                    season_str = ", ".join([f"{s[0]}–{s[1]}" for s in season])
                    bot.send_message(channel_id, f"Medību sezona: {animal.replace('_', ' ').capitalize()} — {season_str}")
                else:
                    bot.send_message(channel_id, "Par šo dzīvnieku/putnu informācija nav pieejama.")

        return make_response("", 200)

    return make_response("No payload", 400)
