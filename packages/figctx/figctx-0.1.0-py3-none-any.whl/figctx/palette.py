from matplotlib.colors import ListedColormap, LinearSegmentedColormap

palette_categorical = [
    '#FF1F5B', '#00CD6C', '#009ADE',
    '#AF58BA', '#FFC61E', '#F28522',
    '#A0B1BA', '#A6761D'
]

palette_blue = [
    '#0D4A70', '#226E9C', '#3C93C2',
    '#6CB0D6', '#9EC9E2', '#C5E1EF',
    '#E4F1F7',
]

palette_green = [
    '#003147', '#045275', '#00718B',
    '#089099', '#46AEA0', '#7CCBA2',
    '#B7E6A5'
]

palette_grass = [
    '#06592A', '#228B3B', '#40AD5A',
    '#6CBA7D', '#9CCEA7', '#CDE5D2',
    '#E1F2E3'
]

palette_warm = [
    '#6E005F', '#AB1866', '#D12959',
    '#E05C5C', '#F08F6E', '#FABF78',
    '#FCE1A4'
]

palette_pink = [
    '#8F003B', '#C40F5B', '#E32977',
    '#E95694', '#ED85B0', '#F2ACCA',
    '#F9D8E6'
]

palette_orange = [
    '#B10026', '#E31A1C', '#FC4E2A',
    '#FDBD3C', '#FEB24C', '#FED976',
    '#FFF3B2'
]

# palette_test = [
#     '#003147', '#005A6D', '#008683',
#     '#31B184', '#93D878', '#F9F871'
# ]


cmap_blue = ListedColormap(palette_blue, 'cmap_blue')
heatmap_blue = LinearSegmentedColormap.from_list('heatmap_blue', palette_blue)


cmap_green = ListedColormap(palette_green, 'cmap_green')
heatmap_green = LinearSegmentedColormap.from_list('heatmap_green', palette_green)


cmap_grass = ListedColormap(palette_grass, 'cmap_grass')
heatmap_grass = LinearSegmentedColormap.from_list('heatmap_grass', palette_grass)


cmap_warm = ListedColormap(palette_warm, 'cmap_warm')
heatmap_warm = LinearSegmentedColormap.from_list('heatmap_warm', palette_warm)


cmap_pink = ListedColormap(palette_pink, 'cmap_pink')
heatmap_pink = LinearSegmentedColormap.from_list('heatmap_pink', palette_pink)


cmap_orange = ListedColormap(palette_orange, 'cmap_orange')
heatmap_orange = LinearSegmentedColormap.from_list('heatmap_orange', palette_orange)
