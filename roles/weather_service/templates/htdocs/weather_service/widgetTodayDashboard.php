<?php
$ch = curl_init();

curl_setopt($ch, CURLOPT_URL, $_SERVER["REQUEST_SCHEME"] . "://" . $_SERVER["SERVER_NAME"]  . "/weather_service/api/widgetData/");
curl_setopt($ch, CURLOPT_POST, 1);
curl_setopt($ch, CURLOPT_POSTFIELDS, "mode=habpanel");

curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

$result = curl_exec($ch);
curl_close($ch);

$values = json_decode($result, true);

/******* OVERVIEW ************/
$blockConfigs = array(
	'21' => array( 'title' => "Nachts", 'class' => 'night' ),
	'16' => array( 'title' => "Abends", 'class' => 'evening' ),
	'11' => array( 'title' => "Mittags", 'class' => 'lunch' ),
	'06' => array( 'title' => "Früh", 'class' => 'morning' ),
	'00' => array( 'title' => "Nachts", 'class' => 'night' ),
);

$blockHours = [];
foreach( $values["dayList"] as $blockData )
{
    $start_hour = DateTime::createFromFormat("Y-m-d\TH:i:sP",$blockData["start"])->format("H");
    $end_hour = DateTime::createFromFormat("Y-m-d\TH:i:sP",$blockData["end"])->format("H");

    $diff = ( $end_hour - $start_hour );
    if( $diff < 0 ) $diff += 24;
    $hour = $start_hour;

    foreach( $blockConfigs as $_hour => $_data )
    {
        if( $hour >= $_hour )
        {
            $hour = $_hour;
            break;
        }
    }

    $blockHours[$blockData["start"]] = $hour;
}

function getSVG( $icon, $id)
{
    return file_get_contents('icons/svg/' . $id . '.svg');
}

function formatDuration($duration)
{
    if( $duration < 180 ) return "<div class=\"value suffixDurationMinute\">" . $duration . "</div>";
    return "<div class=\"value suffixDurationHour\">" . round( $duration / 60 ) . "</div>";
}

function formatNumber($number, $precission = 1)
{
    return number_format($number, $precission);
}

//echo print_r($values,true);
?>
<html><body>
<style>
:root {
    /*--widget-title-color: black;
    --widget-title-size: 1.6em;
    --widget-title-group-color: black;
    --widget-title-group-size: 2em;

    --widget-text-color: black;
    --widget-text-color-nonimportant: #AAA;

    --widget-value-color: black;
    --widget-value-weight: 300;

    --widget-value-size: 1.6em;
    --widget-value-main-size: 3.2em;
    --widget-value-main-sub-size: 1.7em;
    --widget-value-main-icon-size: 3.8em;
    --widget-value-huge-main-size: 4.0em;
    --widget-value-huge-sub-size: 2.8em;
    --widget-value-info-size: 2em;

	--widget-value-color-weather-needle: black;
	--widget-value-color-weather-circle: var(--primary-light-color);
    --widget-value-color-weather-info-icon: var(--sub-icon-color);
    --widget-value-color-weather-clouds: black;
    --widget-value-color-weather-sun: rgba(255, 165, 0, 0.7);
    --widget-value-color-weather-raindrop: black;
    --widget-value-color-weather-snowflake: black;
	--widget-value-color-weather-thunder: rgba(255, 165, 0, 0.6);
	--widget-value-color-weather-thunder-stroke: rgba(255, 165, 0, 0.8);

	--widget-button-border: 1px solid var(--primary-light-color);
    --widget-button-background: rgba(38,191,117,.1);

    --widget-button-border-active: 1px solid var(--primary-color);
    --widget-button-background-active: var(--primary-dark-color);

	--widget-button-border-marker: 1px solid rgba(38,191,117,.1);
	--widget-button-background-marker: #1f1f1f;

	--widget-button-border-hidden: 1px solid transparent;

    --widget-button-background-slider: #0d472a;

    --widget-button-color: black;
    --widget-button-size: 1.4em;
    --widget-button-small-size: 1.3em;
    --widget-button-weight: 200;

    --primary-color: #26bf75;
    --primary-light-color: rgba(38,191,117,.50);
    --primary-dark-color: #09301d;

    --primary-icon-color: var(--primary-dark-color);

    --top-icon-color: rgb(33, 33, 33);
    --sub-icon-color: rgb(33, 33, 33);

	--svg-image-color: rgba(38,191,117,.75);

    --widget-light-color: yellow;

    --widget-error-color: red;
    --widget-warn-color: #ffa500;

    --svg-rollershutter-closed-color: rgba(38,191,117,1.0);
    --svg-rollershutter-advise-color: #ffa500;
    --svg-window-open-color: red;*/

    --title-color: #FFFFFFAA;

    --sub-icon-color: white;
    --widget-value-weight: 300;

    --widget-value-color-weather-clouds: white;
    --widget-value-color-weather-sun: rgba(255, 165, 0, 0.7);
    --widget-value-color-weather-raindrop: white;
    --widget-value-color-weather-snowflake: white;
	--widget-value-color-weather-thunder: rgba(255, 165, 0, 0.6);
	--widget-value-color-weather-thunder-stroke: rgba(255, 165, 0, 0.8);
}
body {
    height: 118px;
    overflow: hidden;
    background-color: #1c1c1d;
    color: white;
    padding: 0;
    margin: 0;
    font-weight: 250;
    font-size: 19px;
    font-family: Roboto, system-ui, Noto, Helvetica, Arial, sans-serif;
}
.weatherForecast svg {
    --svg-weather-mask-fill: white;
    --svg-weather-clouds-stroke: var(--widget-value-color-weather-clouds);
    --svg-weather-clouds-stroke-width: 1px;
    --svg-weather-clouds-fill: transparent;
    --svg-weather-sun-stroke: var(--widget-value-color-weather-sun);
    --svg-weather-sun-stroke-width: 1px;
    --svg-weather-sun-fill: var(--widget-value-color-weather-sun);
    --svg-weather-moon-stroke: var(--widget-value-color-weather-clouds);
    --svg-weather-moon-stroke-width: 1px;
    --svg-weather-moon-fill: transparent;
    --svg-weather-stars-stroke: var(--widget-value-color-weather-clouds);
    --svg-weather-stars-stroke-width: 0.5px;
    --svg-weather-stars-fill: transparent;
    --svg-weather-thunder-stroke: var(--widget-value-color-weather-thunder-stroke);
    --svg-weather-thunder-stroke-width: 1px;
    --svg-weather-thunder-fill: var(--widget-value-color-weather-thunder);
    --svg-weather-raindrop-stroke: var(--widget-value-color-weather-clouds);
    --svg-weather-raindrop-stroke-width: 2px;
    --svg-weather-raindrop-fill: var(--widget-value-color-weather-raindrop);
    --svg-weather-snowflake-stroke: var(--widget-value-color-weather-clouds);
    --svg-weather-snowflake-stroke-width: 1px;
    --svg-weather-snowflake-fill: var(--widget-value-color-weather-snowflake);
}
.main.suffixCelsius::after {
    font-size: 13px;
}
.suffixDurationMinute::after,
.suffixDurationHour::after,
.suffixSpeed::after,
.suffixPercent::after,
.suffixAmmount::after,
.suffixCelsius::after {
    font-size: 11px;
    vertical-align: text-top;
    opacity: 0.7;
    font-weight: 200;
}
.suffixPercent::after {
    content: " %";
}
.suffixAmmount::after {
    content: " mm";
}
.suffixCelsius::after {
    content: " °C";
}
.suffixSpeed::after {
    content: " km/h";
}
.suffixDurationHour::after {
    content: " h";
}
.suffixDurationMinute::after {
    content: " min";
}
.temperature .main .suffixCelsius::after {
    opacity: 0.7;
}

.weatherForecast .sun .day {
	stroke-width: 1.2px;
}
.weatherForecast .sun .night {
	stroke-width: 1.4px;
}

.weatherForecast .details {
    display: flex;
    justify-content: space-between;
}
.weatherForecast .details .value {
    font-weight: 300;
}
.weatherForecast .details .value.temperature {
    display: flex;
}

.weatherForecast .details .value.bottom {
    display: flex;
    position: relative;
    font-size: 14px;
}
.weatherForecast .details .value.bottom .sun {
    overflow: hidden;
    width: 45px;
    height: 45px;
}
.weatherForecast .details .value.bottom .sun svg {
    margin-top: -3px;
}
.weatherForecast .details .value.bottom .precipitationProbability svg {
    width: 0.8em;
    height: 0.8em;
    margin-top: 0.1em;
    margin-right: 2px;
    stroke: var(--sub-icon-color);
    fill: none;
}
.weatherForecast .details .value.bottom .precipitationProbability {
    position: absolute;
    right: 0;
    bottom: 25px;
}
.weatherForecast .details .value.bottom .precipitationAmount {
    position: absolute;
    right: 0;
    bottom: 5px;
}
.weatherForecast .details .value.bottom .value {
    display: flex;
    font-weight: var(--widget-value-weight);
}
.weatherForecast .details .cell {
    padding-bottom: 5px;
}
.weatherForecast .details .cell.title {
    padding-bottom: 7px;
    font-size: 16px;
    opacity: 0.8;
    font-weight: 200;
    color: var(--title-color);
}
.weatherForecast .details .cell .temperature .main {
    font-size: 26px;
}

.weatherForecast .summary {
    font-size: 14px;
    justify-content: space-between;
    padding-top: 5px;
}

.weatherForecast .summary,
.weatherForecast .summary .cell {
    display: flex;
}
.weatherForecast .summary .cell {
    justify-content: space-between;
}
.weatherForecast .summary .cell .value {
    font-weight: var(--widget-value-weight);
}
.weatherForecast .summary .cell .txt {
    opacity: 0.8;
    font-weight: 200;
}
.weatherForecast .summary .icon {
    margin-top: 0.3em;
    margin-left: 0.3em;
    margin-right: 0.3em;
    width: 0.7em;
    height: 0.7em;
    flex-grow: 0;
}
.weatherForecast .summary .icon svg {
    stroke: var(--sub-icon-color);
    fill: var(--sub-icon-color);
    width: auto;
    height: auto;
}
.weatherForecast .summary .icon.rain svg {
    stroke: var(--sub-icon-color);
    fill: none;
    filter: brightness(150%);
}
.weatherForecast .summary .icon.sun svg {
    filter: brightness(70%);
}

</style>
<script>
setTimeout(function() { window.location.reload(true); }, 3600 * 1000);
</script>
<div class="weatherForecast">
	<div class="details">
<?php
    foreach( $values["dayList"] as $blockData ){
        $start = DateTime::createFromFormat("Y-m-d\TH:i:sP",$blockData["start"]);
        $end = DateTime::createFromFormat("Y-m-d\TH:i:sP",$blockData["end"]);
?>
        <div class="block">
            <div class="cell title"><?php echo $start->format("H:i") . ' • ' . $blockConfigs[$blockHours[$blockData["start"]]]['title']; ?></div>
            <div class="cell">
                <div class="value temperature">
                    <div class="main"><?php echo formatNumber($blockData["minAirTemperatureInCelsius"]); ?></div>
                    <div class="main">&nbsp;/&nbsp;</div>
                    <div class="main suffixCelsius"><?php echo formatNumber($blockData["maxAirTemperatureInCelsius"]) ; ?></div>
                </div>
            </div>
            <div class="cell">
                <div class="value bottom">
                    <div class="sun"><?php echo $values["cloudIconMap"][$blockData["cloudIconNames"][0]]; ?>
                    </div>
                    <div class="value precipitationProbability">
                        <?php echo getSVG('rain', 'rain_grayscaled') . "<div class=\"main suffixPercent\">" . formatNumber($blockData["precipitationProbabilityInPercent"], 0); ?></div>
                    </div>
                    <div class="value precipitationAmount">
                        <div class="main suffixAmmount"><?php echo formatNumber($blockData["precipitationAmountInMillimeter"]); ?></div>
                    </div>
                </div>
            </div>
        </div>
<?php } ?>
	</div>
	<div class="summary">
		<div class="cell"><div class="txt">Min.:</div><div class="icon temperature"><?php echo getSVG('temperature', 'temperature_grayscaled') . "</div><div class=\"value suffixCelsius\">" . formatNumber($values["dayMinTemperature"]); ?></div></div>
		<div class="cell"><div class="txt">Max.:</div><div class="icon temperature"><?php echo getSVG('temperature', 'temperature_grayscaled') . "</div><div class=\"value suffixCelsius\">" . formatNumber($values["dayMaxTemperature"]); ?></div></div>
		<div class="cell"><div class="txt">Max.:</div><div class="icon wind"><?php echo getSVG('wind', 'wind_grayscaled') . "</div><div class=\"value suffixSpeed\">" . formatNumber($values["dayMaxWindSpeed"]); ?></div></div>
		<div class="cell"><div class="txt">Sum:</div><div class="icon rain"><?php echo getSVG('rain', 'rain_grayscaled') . "</div><div class=\"value suffixAmmount\">" . formatNumber($values["daySumRain"]); ?></div></div>
		<div class="cell"><div class="txt">Dauer:</div><div class="icon sun"><?php echo getSVG('sun', 'sun_grayscaled') . "</div>" . formatDuration( $values["daySumSunshine"] ); ?></div>
	</div>
</div>
</body></html>
