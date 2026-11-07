DOMAIN = "awenta_ahr"

PLATFORMS = ["fan", "sensor", "binary_sensor", "select"]

API_URL = "https://ahr.awenta.pl/api.php"
WS_URL = "wss://ahr.awenta.pl:31990/"

MANUFACTURER = "Awenta"
MODEL = "HRV"

# Pole z ramki WebSocket: czas pozostały do wymiany filtra w godzinach
# (to samo, co aplikacja Awenta pokazuje jako "stan filtra", np. 2160 h).
# Gdy dojdzie do 0, rekuperator sygnalizuje wymianę filtra mruganiem diody.
KEY_FILTER_TIME_LEFT = "time_filter_time_left"
