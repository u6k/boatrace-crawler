from scrapy import Field, Item


class RaceIndexItem(Item):
    url = Field()
    timestamp = Field()
    place_id = Field()
    place_name = Field()
    race_grade = Field()
    race_name = Field()
    race_index_urls = Field()


class RaceProgramItem(Item):
    url = Field()
    timestamp = Field()
    start_time = Field()
    course_length = Field()


class RaceProgramBracketItem(Item):
    url = Field()
    timestamp = Field()
    bracket_number = Field()
    racer_data1 = Field()
    racer_data2 = Field()
    racer_data3 = Field()
    racer_rate_all_place = Field()
    racer_rate_current_place = Field()
    motor_rate = Field()
    boat_rate = Field()


class RaceProgramBracketResultsItem(Item):
    url = Field()
    timestamp = Field()
    bracket_number = Field()
    run_number = Field()
    bracket_color = Field()
    race_round = Field()
    approach_course = Field()
    start_timing = Field()
    result = Field()


class OddsItem(Item):
    url = Field()
    timestamp = Field()
    bracket_number_1 = Field()
    bracket_number_2 = Field()
    bracket_number_3 = Field()
    odds = Field()


class RaceResultTimeItem(Item):
    url = Field()
    timestamp = Field()
    result = Field()
    bracket_number = Field()
    result_time = Field()


class RaceBeforeBracketItem(Item):
    url = Field()
    timestamp = Field()
    bracket_number = Field()
    racer_href = Field()
    weight = Field()
    weight_adjust = Field()
    time = Field()
    tilt = Field()
    propeller = Field()
    parts_replacement = Field()


class RaceBeforeStartItem(Item):
    url = Field()
    timestamp = Field()
    bracket_number = Field()
    start_time = Field()


class RaceBeforeWeatherItem(Item):
    url = Field()
    timestamp = Field()
    direction = Field()
    temperature = Field()
    weather = Field()
    wind_speed = Field()
    wind_direction = Field()
    water_temperature = Field()
    wave_height = Field()


class RaceResultStartTimeItem(Item):
    url = Field()
    timestamp = Field()
    bracket_number = Field()
    start_time = Field()


class RaceResultWeatherItem(Item):
    url = Field()
    timestamp = Field()
    direction = Field()
    temperature = Field()
    weather = Field()
    wind_speed = Field()
    wind_direction = Field()
    water_temperature = Field()
    wave_height = Field()


class RaceResultPayoffItem(Item):
    url = Field()
    timestamp = Field()
    bet_type = Field()
    bracket_number = Field()
    payoff = Field()
    favorite = Field()


class RacerItem(Item):
    url = Field()
    timestamp = Field()
    name = Field()
    name_kana = Field()
    racer_id = Field()
    birth_day = Field()
    height = Field()
    weight = Field()
    blood_type = Field()
    belong_to = Field()
    birth_place = Field()
    debut_period = Field()
    racer_class = Field()
