import os
os.environ["USERPROFILE"] = "C:\\Users\\User"
import sys
import json
import requests
import numpy as np
import geopandas as gpd
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
import mysql.connector as connector
from dotenv import load_dotenv

load_dotenv()

# path_to_laravel_storage = "C:\laragon\www\prsd-cms-reactjs\storage\\app\public"
path_to_laravel_storage = os.getenv("LARAVEL_STORAGE_PATH")

areas_font_color = "#03021E"
pill_height = 27
margin = 5
line_space = 15
max_width = 620
space_area = 375
start_position = (26, 162)



def set_path(path):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(BASE_DIR, path);

areas_font = ImageFont.truetype(set_path("fonts/inter/Inter-Light-BETA.otf"), size=13)
hazard_font = ImageFont.truetype(set_path("fonts/inter/Inter-SemiBold.otf"), size=12)

def format_areas(selected_areas, municipality_count, is_final = False):
    data = {
        "red": {},
        "orange": {},
        "yellow": {},
        "expecting": {},
        "affecting": {}
    }

    final_output = {}

    for item in selected_areas:
        _type = item["type"]
        province = item["province"]
        municipality = item["municipality"]

        if province not in data[_type]:
            data[_type][province] = []

        data[_type][province].append(municipality.replace(" ", ""))

    for _type, provinces in data.items():
        formatted_output = []

        for province, municipalities in provinces.items():
            max_municipalities = municipality_count.get(province, 0)
            current_count = len(municipalities)

            if current_count == max_municipalities:
                formatted_output.append(f"#{province.replace(' ', '')}")
            else:
                municipality_list = ", ".join(municipalities[:])
                formatted_output.append(f"#{province.replace(' ', '')}({municipality_list})")
        
        formatted_output_len = len(formatted_output)

        if formatted_output_len > 1:
            final_output[_type] = ", ".join(formatted_output[:-1]) + " and " + formatted_output[-1]
            
        if formatted_output_len == 1:
            final_output[_type] = formatted_output[0]

    return final_output

def resize_image_by_percentage(image, percentage):
    """Resize an image by a given percentage."""
    new_width = int(image.width * (percentage / 100))
    new_height = int(image.height * (percentage / 100))
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

def wrap_text(text, font, max_width, return_array = False):
    """Dynamically wraps text based on pixel width."""
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        text_width = font.getbbox(test_line)[2]

        if text_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    lines.append(current_line)

    if return_array:
        return lines

    return "\n".join(lines)

def add_text_to_image(
    prsd_code, 
    rainfall_type, 
    rainfall_no, 
    rainfall_issue_option, 
    issued_at, 
    weather_systems, 
    hazards, 
    formatted_areas, 
    image_path
):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)

    if rainfall_issue_option:
        rainfall_issue_option = rainfall_issue_option.upper() + " "
    else:
        rainfall_issue_option = ""

    draw.text(
        (16, 14), 
        rainfall_type.title() + " No." + rainfall_no + " " + rainfall_issue_option + "#" + prsd_code.upper(), 
        fill="white", 
        font=ImageFont.truetype(set_path("fonts/inter/Inter-Bold.otf"), size=32)
    )

    draw.text(
        (16, 68), 
        "Issued at: " + issued_at, 
        fill="black", 
        font=ImageFont.truetype(set_path("fonts/inter/Inter-Medium.otf"), size=20)
    )

    draw.text(
        (16, 102), 
        "Weather Systems: " + weather_systems, 
        fill="black", 
        font=ImageFont.truetype(set_path("fonts/inter/Inter-Medium.otf"), size=20)
    )

    expecting_pill_path = "templates/expecting_pill.png"
    affecting_pill_path = "templates/affecting_pill.png"
    red_pill_path = "templates/red_pill.png"
    orange_pill_path = "templates/orange_pill.png"
    yellow_pill_path = "templates/yellow_pill.png"
    expecting_box_path = "templates/expecting_box.png"
    affecting_box_path = "templates/affecting_box.png"

    if rainfall_type == "thunderstorm advisory":
        expecting_pill_path = "templates/ts_expecting_pill.png"
        affecting_pill_path = "templates/ts_affecting_pill.png"
        expecting_box_path = "templates/ts_expecting_box.png"
        affecting_box_path = "templates/ts_affecting_box.png"


    pills = {
        "expecting":Image.open(set_path(expecting_pill_path)),
        "affecting":Image.open(set_path(affecting_pill_path)), 
        "red":Image.open(set_path(red_pill_path)), 
        "orange":Image.open(set_path(orange_pill_path)), 
        "yellow":Image.open(set_path(yellow_pill_path)) 
    }

    expecting_box = Image.open(set_path(expecting_box_path))
    affecting_box = Image.open(set_path(affecting_box_path))

    expecting_box_position = (812, 545)
    affecting_box_position = (997, 545)

    if rainfall_type == "rainfall warning":
        red_box = Image.open(set_path("templates/red_box.png"))
        orange_box = Image.open(set_path("templates/orange_box.png"))
        yellow_box = Image.open(set_path("templates/yellow_box.png"))
        image.paste(red_box, (726, 545), red_box)
        image.paste(orange_box, (811, 545), orange_box)
        image.paste(yellow_box, (896, 545), yellow_box)
        expecting_box_position = (981, 545)
        affecting_box_position = (1066, 545)


    image.paste(expecting_box, expecting_box_position, expecting_box)
    image.paste(affecting_box, affecting_box_position, affecting_box)

    footer_bold_normal = ImageFont.truetype(set_path("fonts/inter/Inter-ExtraBold.otf"), size=14.33)
    footer_bold_italic = ImageFont.truetype(set_path("fonts/inter/Inter-ExtraBoldItalic.otf"), size=14.33)

    draw.text((644.88, 582), "Please visit:", fill="white", font=footer_bold_normal)
    draw.text(
        (734, 582), 
        "https://www.pagasa.dost.gov.ph/regional-forecast/" + prsd_code.lower(), 
        fill="white", 
        font=footer_bold_italic
    )
    
    y = start_position[1]
    number_of_keys = len(formatted_areas)
    wrapped_areas = dict([(k, wrap_text(v, areas_font, max_width, True)) for k, v in formatted_areas.items() ])
    number_of_lines = ({k: len(v) + (1 if hazards[k] else 0) for k, v in wrapped_areas.items()})
    total_lines = sum(number_of_lines.values())

    for index, (key, value) in enumerate(formatted_areas.items()):

        image.paste(pills[key], (start_position[0], y), pills[key])
        y = y + pill_height + margin
        wrapped_area = wrapped_areas[key]
        wrapped_area_len = len(wrapped_area)

        if hazards[key]:
            draw.text((start_position[0], y), "Associated Hazard: " + hazards[key], font=hazard_font, fill=areas_font_color)
            wrapped_area_len = wrapped_area_len + 1
            y = y + line_space

        for line in wrapped_area:
            _, _, text_width, text_height = draw.textbbox((start_position[0], y), line, font=areas_font)
            draw.text((start_position[0], y), line, font=areas_font, fill=areas_font_color)
            y += line_space

        if total_lines <= int(int((space_area - (pill_height * number_of_keys)) / line_space) * .5):
            y = y + int((space_area / number_of_keys) - ((pill_height + margin)) - (number_of_lines[key] * line_space))
            
        y = y + margin

    image.save(image_path)

    return image_path

db_con = connector.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_DATABASE"),
    user=os.getenv("DB_USERNAME"),
    password=os.getenv("DB_PASSWORD")
)

rainfall_cursor = db_con.cursor()
prsd_cursor = db_con.cursor()
rainfall_cursor.execute("SELECT * FROM rainfalls WHERE id = %s" , (sys.argv[1], ))
rainfall = rainfall_cursor.fetchone()
rainfall_type = rainfall[6]
rainfall_no = rainfall[4]
rainfall_issue_option = rainfall[5]
weather_systems = rainfall[10]
issued_at = rainfall[3].strftime("%B %d, %Y %I:%M %p")
selected_areas = json.loads(rainfall[7])
hazards = {
    "red": rainfall[22],
    "orange": rainfall[21],
    "yellow": rainfall[20],
    "expecting": False,
    "affecting": False
}

prsd_cursor.execute("SELECT * FROM prsds WHERE id = %s" , (sys.argv[2], ))
prsd = prsd_cursor.fetchone()

prsd_code = prsd[2]
selected_provinces = [user['name'] for user in json.loads(prsd[4])]

rainfall_cursor.close()
prsd_cursor.close()
db_con.close()

areas = {
    "red": [],
    "orange": [],
    "yellow": [],
    "expecting": [],
    "affecting": [],
}

map_config = {
    "NLPRSD": {
        "size": 14,
        "offset_x": 350,
        "offset_y": -10,
        "font_size": 16,
    },
    "NCRPRSD": {
        "size": 12,
        "offset_x": 350,
        "offset_y": 2,
        "font_size": 22,
    },
    "SLPRSD": {
        "size":16, 
        "offset_x": 330,
        "offset_y": 0,
        "font_size": 16,
    },
    "VISPRSD": {
        "size":20,
        "offset_x": 245,
        "offset_y": 0,
        "font_size": 12,
    },
    "MINPRSD": {
        "size":16,
        "offset_x": 310,
        "offset_y": 2,
        "font_size": 16,
    }
}[prsd_code]


gdf_provinces = gpd.read_file(set_path("PH_Adm2_ProvDists.shp/PH_Adm2_ProvDists.shp.shp"))
gdf_municipalities = gpd.read_file(set_path("Municipalities/Municipalities.shp"))

if gdf_provinces.crs != gdf_municipalities.crs:
    gdf_municipalities = gdf_municipalities.to_crs(gdf_provinces.crs)

filtered_municipalities = gdf_municipalities[gdf_municipalities["ADM2_EN"].isin(selected_provinces)]
municipality_count = filtered_municipalities.groupby("ADM2_EN").size().to_dict()
filtered_provinces = gdf_provinces[gdf_provinces["adm2_en"].isin(np.unique(filtered_municipalities["ADM2_EN"]))]

for municipality in selected_areas:
    psgc_code = municipality["psgc_code"]
    if "municipality" in municipality:
        if len(psgc_code) == 8:
            psgc_code = "0" + psgc_code
        areas[municipality["type"]].append("PH" + psgc_code)

areas["red"] = np.unique(areas["red"])
areas["orange"] = np.unique(areas["orange"])
areas["yellow"] = np.unique(areas["yellow"])
areas["affecting"] = np.unique(areas["affecting"])
areas["expecting"] = np.unique(areas["expecting"])

fig, ax = plt.subplots(figsize=(15, 15))

filtered_municipalities.plot(ax=ax, color="#D0D4D5", edgecolor="white", linewidth=0.5)
filtered_provinces.plot(ax=ax, color="none", edgecolor="black", linewidth=1)

for index, row in filtered_provinces.iterrows():
    cx, cy = row["geometry"].centroid.x, row["geometry"].centroid.y
    text = plt.text(cx, cy, row["adm2_en"], color="white", fontsize=map_config["font_size"], fontweight="bold", ha="center", va="center")
    text.set_path_effects([path_effects.Stroke(linewidth=3, foreground='black'), path_effects.Normal()])

for red in areas["red"]:
    color_gdf = filtered_municipalities[filtered_municipalities["ADM3_PCODE"] == red]
    color_gdf.plot(ax=ax, color="#F03B20", edgecolor="white", linewidth=0)
    color_gdf = filtered_municipalities[filtered_municipalities["ADM3_PCODE"] == red]
    color_gdf.plot(ax=ax, color="none", edgecolor="white", linewidth=0.5)

for orange in areas['orange']:
    color_gdf = filtered_municipalities[filtered_municipalities["ADM3_PCODE"] == orange]
    color_gdf.plot(ax=ax, color="#FEB24C", edgecolor="white", linewidth=0)
    color_gdf = filtered_municipalities[filtered_municipalities["ADM3_PCODE"] == orange]
    color_gdf.plot(ax=ax, color="none", edgecolor="white", linewidth=0.5)

for yellow in areas['yellow']:
    color_gdf = filtered_municipalities[filtered_municipalities["ADM3_PCODE"] == yellow]
    color_gdf.plot(ax=ax, color="#E4DE48", edgecolor="white", linewidth=0)
    color_gdf = filtered_municipalities[filtered_municipalities["ADM3_PCODE"] == yellow]
    color_gdf.plot(ax=ax, color="none", edgecolor="white", linewidth=0.5)

for expecting in areas['expecting']:
    color_gdf = filtered_municipalities[filtered_municipalities["ADM3_PCODE"] == expecting]

    if rainfall_type == "rainfall advisory" or rainfall_type == "rainfall warning":
        color_gdf.plot(ax=ax, color="#1890F0", edgecolor="white", linewidth=0)
    else:
        color_gdf.plot(ax=ax, color="#ED459A", edgecolor="white", linewidth=0)

    color_gdf = filtered_municipalities[filtered_municipalities["ADM3_PCODE"] == expecting]
    color_gdf.plot(ax=ax, color="none", edgecolor="white", linewidth=0.5)
    
for affecting in areas['affecting']:
    color_gdf = filtered_municipalities[filtered_municipalities["ADM3_PCODE"] == affecting]

    if rainfall_type == "rainfall advisory" or rainfall_type == "rainfall warning":
        color_gdf.plot(ax=ax, color="#000090", edgecolor="white", linewidth=0)
    else:
        color_gdf.plot(ax=ax, color="#3C0A6D", edgecolor="white", linewidth=0)

    color_gdf = filtered_municipalities[filtered_municipalities["ADM3_PCODE"] == affecting]
    color_gdf.plot(ax=ax, color="none", edgecolor="white", linewidth=0.5)


plt.axis("off")

phil_map = prsd_code.lower() + "_philippines_map.png"
plt.savefig(phil_map, dpi=300, bbox_inches="tight", transparent=True)
template = Image.open(set_path("templates/" + os.getenv("IMAGE_TEMPLATE") +".png"))
philippines_map = Image.open(set_path(phil_map))
resize_percentage = map_config["size"]
philippines_map = resize_image_by_percentage(philippines_map, resize_percentage)
template = template.convert("RGBA")
philippines_map = philippines_map.convert("RGBA")

position = (
    # (template.width - philippines_map.width) // 2 + 200, # left-right
    # (template.height - philippines_map.height) // 2 + 20, # top bottom
    (template.width - philippines_map.width) // 2 + map_config["offset_x"], # left-right
    (template.height - philippines_map.height) // 2 + map_config["offset_y"],# top bottom
)

overlay = Image.new("RGBA", template.size, (0, 0, 0, 0))
overlay.paste(philippines_map, position, philippines_map)
result = Image.alpha_composite(template, overlay)
output_image_path = path_to_laravel_storage + "/" + prsd_code.lower()+ "_" + sys.argv[3] + "_warning_map.png"
# output_image_path = set_path(prsd_code.lower()+ "_" + sys.argv[1] + "_" + sys.argv[2] + "_warning_map.png")
result.save(output_image_path)

try:

    add_text_to_image(    
        prsd_code,
        rainfall_type,
        rainfall_no,
        rainfall_issue_option,
        issued_at,
        weather_systems,
        hazards,
        format_areas(selected_areas, municipality_count),
        output_image_path
    )

    print("success")
    
except Exception as e:
    sys.exit(1)
