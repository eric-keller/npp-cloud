terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "4.51.0"
    }
  }
}


resource "google_compute_instance" "mod1-tf-vm1" {
  name = "mod1-tf-vm1"
  machine_type = "e2-micro"
//  zone = "us-central1-a"  
  zone = "us-west1-c"
  network_interface {
    access_config {
      network_tier = "STANDARD"
    }
    network = "default"
  }

  boot_disk {
    initialize_params {
      image = "debian-12-bookworm-v20240312"
      size = 30
      type = "pd-standard"
    }
  } 
  metadata = {
    startup-script = "sudo apt update; sudo apt-get install netcat-traditional;"
  }

}

