from scrapy import Field, Item


class RaceIndexItem(Item):
    url = Field()
    place_id = Field()
    place_name = Field()
    race_grade = Field()
    race_name = Field()
    race_index_urls = Field()


class RaceProgramItem(Item):
    url = Field()
    start_time = Field()
    course_length = Field()


class RaceProgramBracketItem(Item):
    url = Field()
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
    bracket_number = Field()
    run_number = Field()
    bracket_color = Field()
    race_round = Field()
    approach_course = Field()
    start_timing = Field()
    result = Field()
