from scrapy import Field, Item


class RaceIndexItem(Item):
    type = Field()
    place_id = Field()
    place_name = Field()
    race_grade = Field()
    race_name = Field()
    race_index_urls = Field()
