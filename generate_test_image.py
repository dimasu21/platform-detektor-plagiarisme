from PIL import Image, ImageDraw, ImageFont

# Create an image with white background
img = Image.new('RGB', (800, 200), color = (255, 255, 255))
d = ImageDraw.Draw(img)

# Add text
text = "Algoritma Rabin-Karp adalah algoritma pencarian string yang menggunakan hashing."
d.text((10,10), text, fill=(0,0,0))

# Save
img.save('test_suspect.png')
