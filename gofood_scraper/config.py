"""Constants shared across the scraper: URLs, CSS/XPath selectors, and timing."""

CITIES_URL = "https://gofood.co.id/en/cities"

SCROLL_PAUSE_TIME = 1
LOADING_TIME = 2
DRIVER_RESOLVE_TIMEOUT = 30
MAX_RETRY_COUNT = 3

OUTPUT_DIR = "outputs"

XPATH_CITIES_LOADED = '//*[@id="__next"]/div/div[2]/div[2]/div/div/div[2]/a[360]'
XPATH_LOAD_MORE_LINK = '//*[@id="__next"]/div/div[3]/div[2]/button'
XPATH_REVIEW_LINK = '//*[@id="__next"]/div/div[2]/div[1]/div[2]/div/div[1]/div[2]/a'
XPATH_BACK_BUTTON = '//*[@id="__next"]/div/div[2]/div[1]/button'
XPATH_MENU_LINK = '//*[@id="__next"]/div/div[2]/div[1]/div[1]/div[2]/div[2]/div/div'

CLASS_CITY_CARD = "transition-all duration-500 visible relative top-0 block opacity-100 btn-area"
CLASS_RESTAURANT_CARD = (
    "border-b border-gf-background-border-secondary outline-none transition-all "
    "duration-300 ease-in-out last-of-type:border-0 active:!border-transparent "
    "active:bg-gf-interactive-fill-active md:rounded-2xl md:border last-of-type:md:border "
    "hover:md:border-transparent hover:md:gf-shadow-high focus:md:border-gf-interactive-focus"
)
CLASS_BIG_MENU_CARD = "text-gf-content-primary line-clamp-2 gf-label-m"
CLASS_SMALL_MENU_CARD = "mt-1 break-words text-gf-content-muted line-clamp-2 gf-body-s"
CLASS_MENU_CARD = "mt-1 ml-1 mr-4 flex w-full flex-col"
CLASS_RESTAURANT_IMAGE = "overflow-hidden rounded-xl object-cover"
CLASS_RESTAURANT_RATING = (
    "from-gf-background-fill-brand text-gf-content-inverse bg-gradient-to-r to-[#EB525E] "
    "relative flex w-max items-center whitespace-nowrap px-2 py-1 gf-label-s rounded-full "
    "!bg-gf-background-fill-primary !from-transparent !to-transparent !text-gf-content-primary"
)
CLASS_RESTAURANT_NAME = "mb-2 line-clamp-2 gf-label-m"
CLASS_RESTAURANT_TYPE = "mb-2 text-gf-content-secondary line-clamp-1 gf-body-xs md:mb-4 lg:gf-body-s"
CLASS_RESTAURANT_ADDRESS = "text-gf-content-muted gf-body-s"
CLASS_RESTAURANT_PRICE_LEVEL = "text-gf-content-primary"
CLASS_RESTAURANT_PRICE = "shrink-0 grow-0 text-gf-content-primary gf-body-s md:gf-body-m"
CLASS_OPEN_HOURS_ROW = "flex items-center justify-between text-gf-content-secondary md:justify-start"

RESTAURANTS_URL_WITH_DISTRICT = "https://gofood.co.id/{}/{}-restaurants/{}"
RESTAURANTS_URL_WITHOUT_DISTRICT = "https://gofood.co.id/{}/restaurants/{}"
RESTAURANT_URL = "https://gofood.co.id{}"

SCROLL_TO_BOTTOM = "window.scrollTo(0, document.body.scrollHeight);"
SCROLL_TO_TOP = "window.scrollTo(0, document.body.scrollTop);"
SCROLL_UP = "window.scrollBy(0,-400)"
GET_PAGE_HEIGHT = "return document.body.scrollHeight"

CATEGORY_ARR = [
    "Near me",
    "Best sellers",
    "Budget meal",
    "Most loved",
    "24 hours",
    "Healthy food",
    "Pasti Ada Promo",
    "Semua",
]
CATEGORY_LINK_ARR = [
    ["near_me"],
    ["best_seller"],
    ["affordable_price"],
    ["most_loved"],
    ["24_hours"],
    ["healthy_food"],
    ["mkd_megapromo_all"],
    ["near_me", "best_seller", "affordable_price", "most_loved", "24_hours", "healthy_food", "mkd_megapromo_all"],
]

HEADERS = [
    "Link", "Image", "Rating", "Total Rating", "Name", "Type",
    "Total Menu with Inputted Keywords", "Menu with Inputted Keywords", "Address",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    "Gofood Price Level",
]
