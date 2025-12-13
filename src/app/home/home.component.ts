import { Component, ElementRef, ViewChild, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { HeaderComponent } from '../shared/header.component';
import { FooterComponent } from '../shared/footer.component';

// Import PrimeNG modules
import { ButtonModule } from 'primeng/button';

// Interface สำหรับข้อมูลเกม
interface Game {
  id: number;
  title: string;
  image: string;
  rating: number;
  tags: string[];
}

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule,
    RouterLink,
    HeaderComponent,
    FooterComponent,
    ButtonModule
  ],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit, OnDestroy {

  currentSlide = 0;
  autoSlideInterval: any;

  newArrivals: Game[] = [
    {
      id: 1,
      title: 'Naraka: Bladepoint',
      image: 'https://cdn.akamai.steamstatic.com/steam/apps/1203220/header.jpg',
      rating: 4.5,
      tags: ['Action', 'Battle Royale']
    },
    {
      id: 2,
      title: 'Elden Ring',
      image: 'https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg',
      rating: 5.0,
      tags: ['RPG', 'Open World']
    },
    {
      id: 3,
      title: 'Black Myth: Wukong',
      image: 'https://cdn.akamai.steamstatic.com/steam/apps/2358720/header.jpg',
      rating: 4.8,
      tags: ['Action', 'Adventure']
    },
    {
      id: 4,
      title: 'Call of Duty: Black Ops 6',
      image: 'https://cdn.akamai.steamstatic.com/steam/apps/2933620/header.jpg',
      rating: 4.2,
      tags: ['FPS', 'Action']
    }
  ];

  // --- Data ส่วนคะแนนรีวิวสูง ---
  highRatedGames: Game[] = [
    {
      id: 101,
      title: 'Apex Legends',
      image: 'https://cdn.akamai.steamstatic.com/steam/apps/1172470/library_600x900.jpg',
      rating: 4.5, // Fixed rating to be realistic
      tags: ['ยิงปืน', 'เกมไว']
    },
    {
      id: 102,
      title: 'Fallout 4',
      image: 'https://cdn.akamai.steamstatic.com/steam/apps/377160/library_600x900.jpg',
      rating: 5.0,
      tags: ['RPG', 'Open World']
    },
    {
      id: 103,
      title: 'Cyberpunk 2077',
      image: 'https://cdn.akamai.steamstatic.com/steam/apps/1091500/library_600x900.jpg',
      rating: 4.2,
      tags: ['Open World', 'Sci-fi']
    },
    {
      id: 104,
      title: 'God of War',
      image: 'https://cdn.akamai.steamstatic.com/steam/apps/1593500/library_600x900.jpg',
      rating: 4.9,
      tags: ['Action', 'Story Rich']
    },
    {
      id: 105,
      title: 'Stardew Valley',
      image: 'https://cdn.akamai.steamstatic.com/steam/apps/413150/library_600x900.jpg',
      rating: 4.8,
      tags: ['Farming', 'Simulation']
    }
  ];

  @ViewChild('cardList') cardList!: ElementRef;

  ngOnInit() {
    this.startAutoSlide();
  }

  ngOnDestroy() {
    this.stopAutoSlide();
  }

  startAutoSlide() {
    this.autoSlideInterval = setInterval(() => {
      this.nextSlide();
    }, 5000);
  }

  stopAutoSlide() {
    if (this.autoSlideInterval) {
      clearInterval(this.autoSlideInterval);
    }
  }

  // --- Logic สำหรับ Hero Slider ---
  prevSlide() {
    this.stopAutoSlide(); // Reset timer if manually clicked
    this.currentSlide = (this.currentSlide === 0) ? this.newArrivals.length - 1 : this.currentSlide - 1;
    this.startAutoSlide(); // Restart timer
  }

  nextSlide() {
    this.currentSlide = (this.currentSlide === this.newArrivals.length - 1) ? 0 : this.currentSlide + 1;
  }

  // Method for manual next button click (resets timer)
  manualNext() {
    this.stopAutoSlide();
    this.nextSlide();
    this.startAutoSlide();
  }

  // --- Logic สำหรับ High Rated Scroll ---
  scrollList(offset: number) {
    this.cardList.nativeElement.scrollBy({ left: offset, behavior: 'smooth' });
  }
}