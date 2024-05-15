provider "google" {
  credentials = file("../orbital-linker-398719-c59c16fa0cce.json")

  project = "orbital-linker-398719"
  region  = "us-central1"  // default
  zone    = "us-central1-c"  // default
}
