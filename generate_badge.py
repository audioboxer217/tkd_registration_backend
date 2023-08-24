from PIL import Image, ImageDraw, ImageFont

# Opening the template image as the main badge
badge = Image.open(r"img/id_template.png")

# Opening and resizing the profile image
profile_img = Image.open(r"jensen.jpg")
profile_img = profile_img.resize((590, 585))

# Place profile image on background
badge.paste(profile_img, (301, 123))

# Add text items
font = ImageFont.truetype("img/OpenSans-Regular.ttf", size=65)
badge_draw = ImageDraw.Draw(badge)
# Ring Number
badge_draw.text((150, 175), "1", font=font, fill="white")
# ID Number
badge_draw.text((1000, 175), "3", font=font, fill="white")
# Gender
badge_draw.text((190, 960), "F", font=font, fill="black")
# Age
badge_draw.text((190, 1050), "11", font=font, fill="black")
# Belt
badge_draw.text((925, 960), "Black", font=font, fill="black")
# Weight
badge_draw.text((925, 1050), "77 kg", font=font, fill="black")
# Events
events = ["sparring", "poomsae"]
y = 1300
for event in events:
    badge_draw.text((150, y), f"• {event}", font=font, fill="black")
    y += 100

# Save the image
badge = badge.convert("RGB")
badge.save("jensen_badge.jpg")
