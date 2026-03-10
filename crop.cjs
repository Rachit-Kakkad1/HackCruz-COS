const Jimp = require('jimp');

async function crop() {
    try {
        console.log("Reading image...");
        const img = await Jimp.read('public/logo.png');
        const w = img.bitmap.width;
        const h = img.bitmap.height;

        console.log(`Original Size: ${w}x${h}`);

        // The logo text is at the bottom, so let's crop a square from the upper-middle section
        // We'll crop 70% of the image size, starting 15% from the top and 15% from the left to center it tightly around the sphere
        const cropSize = Math.floor(w * 0.70);
        const xOffset = Math.floor(w * 0.15);
        const yOffset = Math.floor(h * 0.15);

        console.log(`Cropping square of size ${cropSize} at x:${xOffset}, y:${yOffset}`);

        img.crop(xOffset, yOffset, cropSize, cropSize)
            .write('public/logo.png');

        console.log("Cropped successfully to public/logo.png!");
    } catch (e) {
        console.error("Error cropping image:", e);
    }
}
crop();
