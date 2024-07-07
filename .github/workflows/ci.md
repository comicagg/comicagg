# CI Workflow for Docker images

## PR push

   >Make sure the image builds correctly, push manually to repository if repro needed.

   - Tag with the PR name
   - Push to repository if parameter
   - If changes to requirements.txt
      - Build python, else use last development

## Development push

   >Push to dev branch, so the PR was accepted.

   - Tag with development
   - If changes to requirements
      - Build python, else use last development.

## Tag push

   >New stable version, push as latest and tag

   - Always build Python image
   - Tag both with tag and latest
   - Always push to repository
