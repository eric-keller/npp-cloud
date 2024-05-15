
//https://registry.terraform.io/providers/hashicorp/google/latest/docs/guides/provider_reference
provider "google" {
  credentials = file("FILL-IN.json")

  project = "FILL-IN"
  region  = "us-central1"
  zone    = "us-central1-c"
}
