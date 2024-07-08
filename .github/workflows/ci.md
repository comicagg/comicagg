# CI Workflow for Docker images

## Development push

   >Push to dev branch, so the PR was accepted.

   - Tag with development
   - If changes to requirements
      - Build python, else use last development.
   - Push images to repository

## Tag push

   >New stable version, push as latest and tag.

   - Always build Python image
   - Tag both with tag and latest
   - Push images to repository

## PR push

   >Make sure the image builds correctly, push manually to repository if repro needed.

   - Tag with the PR name
   - Push to repository if workflow input
   - If changes to requirements.txt
      - Build python, else use last development
