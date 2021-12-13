# S3 bucket was setup manually, and we don't want to manage it here
data "aws_s3_bucket" "bucket" {
}

resource "aws_lambda_function" "s3lambda" {
  filename      = "${path.module}/llp-tag-expires/lambda.zip"
  function_name = "llp-tag-expires"
  role          = aws_iam_role.s3_lambda_role.arn
  handler       = "index.lambda_handler"
  runtime       = "python3.8"
  depends_on    = [aws_iam_role_policy_attachment.logging_policy_attach]
}


resource "aws_s3_bucket_notification" "s3_bucket_notification" {
    bucket = data.bucket.id
    lambda_function {
        lambda_function_arn = aws_lambda_function.s3lambda.arn
        events              = ["s3:ObjectCreated:*"]
    }
    depends_on = [
        aws_iam_role_policy_attachment.logging_policy_attach,
        aws_lambda_permission.allow_bucket,
        aws_lambda_function.s3lambda
    ]
}

resource "aws_iam_role" "s3_lambda_role" {
    name               = "s3_lambda_function_role"
    assume_role_policy = <<EOF
    {
        "Version": "2012-10-17",
        "Statement": [
            {
            "Action": "sts:AssumeRole",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Effect": "Allow"
            }
        ]
    }
    EOF
}


# IAM policy for logging from a lambda
resource "aws_iam_policy" "lambda_tagging" {
    name        = "LambdaTaggingPolicy"
    path        = "/"
    description = "Tags files to be expired based on paths"
    policy      = <<EOF
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "VisualEditor0",
                "Effect": "Allow",
                "Action": "s3:PutObjectTagging",
                "Resource": "${data.bucket.arn}/*"
            },
        ]
    }
    EOF
}

resource "aws_iam_role_policy_attachment" "tagging_policy_attach" {
    role       = aws_iam_role.s3_lambda_role.name
    policy_arn = aws_iam_policy.lambda_tagging.arn
}
