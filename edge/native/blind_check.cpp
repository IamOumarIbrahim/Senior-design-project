//   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
//        Oumar Mamoun Ibrahim U22200741
//        Abdullah Jafar Abdelhamid U23101327
//        Faris Munadhil Ahmed Alagha U23104246
//        Mohamed Ahmed Saad Khafagy U20101649

// the two numbers of the camera blind check, this runs on every frame
// it has to give the same answer as the opencv code in preprocessor.py
//   gray      same as cv2.cvtColor BGR2GRAY
//   laplacian same as cv2.Laplacian ksize 1, the border is reflect 101

#include <stdlib.h>

#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT
#endif

// reflect 101 means -1 becomes 1 and size becomes size - 2
static int border(int i, int size) {
    if (size == 1) {
        return 0;
    }
    if (i < 0) {
        return -i;
    }
    if (i >= size) {
        return 2 * size - 2 - i;
    }
    return i;
}

// img is bgr, stride is the bytes in one row
// returns 0 if it worked
extern "C" EXPORT int blind_numbers(const unsigned char* img, int h, int w, int stride, double* bright, double* sharp) {
    unsigned char* gray = (unsigned char*)malloc((size_t)h * w);
    if (gray == NULL) {
        return 1;
    }

    long long total = 0;
    for (int y = 0; y < h; y++) {
        const unsigned char* p = img + (long long)y * stride;
        unsigned char* g = gray + (long long)y * w;
        for (int x = 0; x < w; x++) {
            // fixed point weights from opencv, 15 bits, same as cv2 on all 16 million colours
            g[x] = (unsigned char)((p[3 * x] * 3735 + p[3 * x + 1] * 19235 + p[3 * x + 2] * 9798 + 16384) >> 15);
        }
        int row = 0;
        for (int x = 0; x < w; x++) {
            row = row + g[x];
        }
        total = total + row;
    }

    long long sum = 0;
    long long sum2 = 0;
    for (int y = 0; y < h; y++) {
        const unsigned char* g = gray + (long long)y * w;
        const unsigned char* up = gray + (long long)border(y - 1, h) * w;
        const unsigned char* down = gray + (long long)border(y + 1, h) * w;

        // first and last pixel of the row need the border
        int ends[2];
        ends[0] = 0;
        ends[1] = w - 1;
        for (int k = 0; k < 2; k++) {
            int x = ends[k];
            if (k == 0 || w > 1) {
                int v = up[x] + down[x] + g[border(x - 1, w)] + g[border(x + 1, w)] - 4 * g[x];
                sum = sum + v;
                sum2 = sum2 + v * v;
            }
        }

        // the rest of the row, kept as a plain loop so the compiler can use simd
        int part = 0;
        long long part2 = 0;
        for (int x = 1; x < w - 1; x++) {
            int v = up[x] + down[x] + g[x - 1] + g[x + 1] - 4 * g[x];
            part = part + v;
            part2 = part2 + v * v;
        }
        sum = sum + part;
        sum2 = sum2 + part2;
    }
    free(gray);

    double n = (double)h * w;
    *bright = total / n;
    // var = mean of the squares - square of the mean
    *sharp = (n * sum2 - (double)sum * sum) / (n * n);
    return 0;
}
