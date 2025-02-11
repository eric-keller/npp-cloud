terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "4.51.0"
    }
  }
}


// Note: If you need to reference the outputs (assigned values)
// https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_subnetwork#id
// https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_network#id


// Create the VPC

resource "google_compute_network" "tf-mod2-demo1-network1" {
  name = "tf-mod2-demo1-network1"
  auto_create_subnetworks = "false"
}


// Create the subnet
// https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_subnetwork

resource "google_compute_subnetwork" "tf-mod2-demo1-subnet1" {
  name          = "tf-mod2-demo1-subnet1"
  ip_cidr_range = "10.2.0.0/16"
  region        = "us-central1"
  network       = google_compute_network.tf-mod2-demo1-network1.id
}



// Create Firewall rule - allow icmp, tcp:22 (ssh), and tcp:1234 (custom)
//https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_firewall
resource "google_compute_firewall" "tf-mod2-demo1-fwrule1" {
  project = "FILL-IN"
  name        = "tf-mod2-demo1-fwrule1"
  network     = "tf-mod2-demo1-network1"
  // need the network created before the firewall rule
  // I noticed sometimes terraform didn't detect the dependency, so making explicit.
  depends_on = [google_compute_network.tf-mod2-demo1-network1]

  allow {
    protocol  = "tcp"
    ports     = ["22", "1234"]
  }
  allow {
    protocol = "icmp"
  }
  source_ranges = ["0.0.0.0/0"]
}




// Create a VM, and put it inside of subnet1
// https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_instance
resource "google_compute_instance" "tf-mod2-demo1-vm1" {
  name = "tf-mod2-demo1-vm1"
  machine_type = "e2-micro"
  zone = "us-central1-a"  
  depends_on = [google_compute_network.tf-mod2-demo1-network1, google_compute_subnetwork.tf-mod2-demo1-subnet1]
  network_interface {
    // This indicates to give a public IP address
    access_config {
      network_tier = "STANDARD"
    }
    network = "tf-mod2-demo1-network1"
    subnetwork = "tf-mod2-demo1-subnet1"
  }

  boot_disk {
    initialize_params {
      image = "debian-12-bookworm-v20240312"
    }
  } 
  metadata = {
    startup-script = "sudo apt update; sudo apt -y install netcat-traditional ncat;"
  }

}

//terraform show -json | jq

// If you see something like this:
// │ Error: Error creating instance: googleapi: Error 400: Invalid value for field 'resource.networkInterfaces[0].subnetwork': 'projects/orbital-linker-398719/regions/us-central1/subnetworks/tf-mod2-demo1-subnet1'. The referenced subnetwork resource cannot be found., invalid
// There's a dependency that terraform didn't resolve, so it's trying to create X which depends on Y existing.
// To solve, use depends_on
