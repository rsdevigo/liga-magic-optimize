"""LigaMagic CSS selectors - single maintenance point."""

# Search page
SEARCH_INPUT = "input#mainsearch, input[name='card'], input#card, input[placeholder*='carta'], input[type='search']"
SEARCH_FORM = "form[action*='busca'], form.search-form"
AUTOCOMPLETE_LIST = "ul.ui-autocomplete li, .autocomplete-list li, .ui-menu-item"
AUTOCOMPLETE_ITEM = "ul.ui-autocomplete li a, .autocomplete-list li a, .ui-menu-item a"

# Card page / offers
MARKETPLACE_STORE = "#marketplace-stores .store, .stores .store"
MARKETPLACE_STORE_LINK = "a.link-store[href*='id=']"
MARKETPLACE_PRICE = ".left-content .new-price, .price .new-price"
MARKETPLACE_CONDITION = ".quality"
MARKETPLACE_LANGUAGE = ".lang img[title], .lang img[alt]"
MARKETPLACE_EDITION = ".name-ed a"
MARKETPLACE_QUANTITY_INPUT = "input[data-id]"

OFFER_TABLE = "table.table, table.lista-vendedores, #lista-vendedores"
OFFER_ROW = (
    "#marketplace-stores .store, .stores.container-tab-1 .store, "
    "table.table tbody tr, table.lista-vendedores tbody tr, .seller-row, tr.vendedor"
)
OFFER_PRICE = "td.preco, .price-value, span.preco, td:nth-child(3)"
OFFER_STORE_NAME = "td.vendedor a, a.seller-name, .nome-vendedor a, td:nth-child(1) a"
OFFER_STORE_LINK = "td.vendedor a, a.seller-name"
OFFER_CONDITION = "td.condicao, .condition-badge, span.condicao, td:nth-child(4)"
OFFER_QUANTITY = "td.quantidade, .stock-quantity, span.qtd, td:nth-child(5)"
OFFER_LANGUAGE = "td.idioma, span.idioma, td:nth-child(6)"
OFFER_EDITION = "td.edicao, span.edicao, td:nth-child(2)"

# Pagination
PAGINATION_NEXT = "a.next, a.proximo, li.next a, .pagination .next a"
PAGINATION_CURRENT = ".pagination .active, .paginacao .atual"

# Anti-bot / captcha
CAPTCHA_CONTAINER = "iframe[src*='captcha'], .g-recaptcha, #captcha, .cf-challenge"

# Card info
CARD_TITLE = "h1.card-name, h1.nome-carta, .card-title h1, h1"
CARD_NOT_FOUND = ".not-found, .sem-resultado, .alert-warning"

# URLs
SEARCH_URL = "/?view=cards/search"
CARD_URL_PATTERN = "/?view=cards/card"
