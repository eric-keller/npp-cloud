provider "google" {
  credentials = file("FILL-IN.json")

  project = "FILL-IN"
  region  = "us-central1"  // default
  zone    = "us-central1-c"  // default
}
