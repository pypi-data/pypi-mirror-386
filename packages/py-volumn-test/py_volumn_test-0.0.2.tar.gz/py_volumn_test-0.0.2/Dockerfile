# Stage 1: Build the package
FROM python:3.12-slim AS builder

# Set the working directory
WORKDIR /app

# Copy the rest of the application source code
COPY . .
RUN bash install-dependencies.sh

RUN rm -fr dist
RUN bash build.sh

# Stage 2: Create the final image
FROM python:3.12-slim AS final

# Set the working directory
WORKDIR /app

# Copy the built wheel from the builder stage
# This pattern will copy the first .whl file found.
COPY --from=builder /app/dist/*.whl .

# Install the wheel.
# We also install runtime dependencies from requirements.txt.
RUN pip install --no-cache-dir /app/*.whl

# Set the entrypoint for the container.
# This will execute your package's __main__.py
CMD ["python", "-m", "py_volumn_test"]