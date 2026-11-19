# Crochet Globe Generator

This tool generates a crochet pattern for a globe of any desired diameter and any type of stitch. 


## Usage

1. Crochet a small test circle, for example starting with 6 sc and increasing by 6 stitches in each round. Measure the width and the height of a single stitch (mm). Observe how the stitches shift from one round to the next. Measure also the resulting offset per round (mm).
2. To obtain an estimate on the expected yarn consumption, count the total number of stitches and unravel the test piece. Measure the length of yarn used (cm).
3. Select whether you want to crochet the whole globe at once or the northern and southern hemisphere separately. Enter all measurements and click **GENERATE**. Depending on the selected size, it may take a few minutes until the crochet pattern and the expected yarn consumption will appear. Note that color changes also require yarn and thus expect a higher yarn consumption depending on the resolution of the globe.
4. Either crochet the entire globe as a single piece and stuff it immediately or or crochet the northern and southern hemispheres separately and join them at the equator. If the globe is used as a pillow case, you may use a red zipper to mark the equator.

## Abbreviations

- `sc` = single crochet
- `inc` = increase
- `dec` = decrease

## Demo
Output:
![Screenshot](images/screenshot.png)
Process of crocheting:
![Screenshot](images/process.jpeg)

## Documentation

- **class Loader**. Input: paths of datasets, creates list of datasets (dss) and list of bounds the covered rectangle (bounds) 
- **lookup**. Input: coordinates of one point, Output: value of the nearest point of the dataset (in our case values from 1 to 20 encoding landscape geodata) 
- **lookup_majority_window**. Input: coordinates of one point, size of the patch, maximal number of samples, Output: Median value of point laying in the patch around the given point 
- **lookup_list_majority_batch_flat**. Input: list of coordinates, patch size, maximal number of samples, Output: flat list of corresponding values 
- **lookup_list_majority_batch_nested**. Same as lookup_list_majority_batch_flat but puts out a nested list values. 
- **class StitchCoordinates**. Input: stitch length, stitch height, stitch setback, globe diameter, calculates number of initial stitches and number of rows 
- **calculate**: Calculates the number of stitches each row and other quantities 
- **coordinates**: Calculates the coordinates of each stitch in each row 
- **doublestitches**: Calculates which stitch in each row is a increase, decrease or single crochet. Returns list of lists with entries in {-1,0,1}. 
- **class PatternGenerator**. Inputs: instance of Loader, instance of StitchCoordinates, Calculates patch size from stitch size, calls `lookup_list_majority_batch_nested` and stores into `farb`. Converts information about stitch type and color into one nested list `self.info`. 
- **info_globe**. Converts information about stitch type and color of the whole globe into one nested list. 
- **info_southern_hemisphere**. Converts information about stitch type and color of the southern hemisphere into one nested list. 
- **info_northern_hemisphere**. Converts information about stitch type and color of the northern hemisphere into one nested list. Differs from the result of the whole globe, because when crocheting the northern hemisphere alone, one starts from the north pole instead of the equator. 
- **statistik**. Returns a dictionary, where each color is assigned to the amount of stitches in that color. 
- **colorword**. Converts an integer in {1,...,20} representing the landscape type to a name of a color in type of a string. 
- **clean_list**. Converts a list in the format of the info-methods into a compact form, handling repetitions.``


