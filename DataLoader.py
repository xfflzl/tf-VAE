import os
import numpy as np
import scipy.io as scio

class DataLoader(object):
    r"""Load data from mnist_all.mat
    
    Args:
      dataFile: Name of .mat file.
      dataPath: Folder of data file.
      train_images_per_digit: Number of training pictures loaded per digit.
      test_images_per_digit: Number of test pictures loaded per digit.
    """
    def __init__(self, dataFile, dataPath='.\\data\\',  
                 train_images_per_digit=5000, test_images_per_digit=800):
        self.dataPath = os.path.join(dataPath, dataFile)
        self.train_images_per_digit = train_images_per_digit
        self.test_images_per_digit = test_images_per_digit

    def obtain_data(self):
        r"""Extract data from .mat file.

        Returns:
          train_images: Pixel matrix of training set. Shape=(num_train_images, image_size ** 2)
          test_images: Pixel matrix of test set. Shape=(num_test_images, image_size ** 2)
          image_size: Pixel-measured side length of one picture.
        """
        dataDict = scio.loadmat(self.dataPath)
        image_size = int(np.sqrt(dataDict['train0'].shape[1]))
        train_images = np.empty([10 * self.train_images_per_digit, image_size ** 2])
        test_images = np.empty([10 * self.test_images_per_digit, image_size ** 2])
        for digit in range(10):
            train_images[digit * self.train_images_per_digit: (digit + 1) * self.train_images_per_digit] = dataDict['train' + str(digit)][: self.train_images_per_digit]
            test_images[digit * self.test_images_per_digit: (digit + 1) * self.test_images_per_digit] = dataDict['test' + str(digit)][: self.test_images_per_digit]
        train_images = train_images / 255.0
        test_images = test_images / 255.0
        np.random.shuffle(train_images)
        np.random.shuffle(test_images)
        return train_images, test_images, image_size
        