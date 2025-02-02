# Digital Wardrobe Image Labeling with AWS Rekognition

This project is a serverless application that uses AWS Rekognition to detect and label clothing items. The labels are then stored in a DynamoDB table. The application is implemented as an AWS Lambda function, which processes images from an S3 bucket and stores the results in DynamoDB.

## Features
    - Image Labeling: Detects labels (e.g., clothing items) in images using AWS Rekognition.
    - Confidence Filtering: Only labels with a confidence score greater than 90% are considered.    


## Usage
    - Upload Images: Upload images of clothing items to the S3 bucket (digital-wardrobe-bucket).
    - Invoke Lambda: The Lambda function will automatically process the images and store the results in the DynamoDB table.
    - View Results: Check the DynamoDB table (wardrobe) to see the image keys and associated labels.

## Example Output
The Lambda function returns a JSON object with the image keys and their associated labels:

`[
  {
    "ImageKey": "image1.jpg",
    "Labels": ["Shirt", "Clothing"]
  },
  {
    "ImageKey": "image2.jpg",
    "Labels": ["Jeans", "Clothing"]
  }
]`

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.