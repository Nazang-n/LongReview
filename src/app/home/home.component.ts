import { Component, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { HeaderComponent } from '../shared/header.component';
import { FooterComponent } from '../shared/footer.component';

// Interface สำหรับข้อมูลเกม (ปกติควรแยกไฟล์ แต่รวมไว้ที่นี่เพื่อความสะดวก)
interface Game {
  id: number;
  title: string;
  image: string;
  rating: number;
  tags: string[];
}

@Component({
  selector: 'app-home',
  standalone: true, // ถ้าโปรเจคไม่ใช่ Standalone ให้ลบ Line นี้และ import CommonModule ใน Module หลัก
  imports: [CommonModule,
            RouterLink,
            HeaderComponent,
            FooterComponent
          ],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent {
  
  // --- Data ส่วน Hero (มาใหม่) ---
  currentSlide = 0;
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
    }
  ];

  // --- Data ส่วนคะแนนรีวิวสูง ---
  highRatedGames: Game[] = [
    {
      id: 101,
      title: 'Apex Legends',
      image: 'https://cdn.akamai.steamstatic.com/steam/apps/1172470/library_600x900.jpg',
      rating: 0.5,
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

  // --- Logic สำหรับ Hero Slider ---
  prevSlide() {
    this.currentSlide = (this.currentSlide === 0) ? this.newArrivals.length - 1 : this.currentSlide - 1;
  }
  
  nextSlide() {
    this.currentSlide = (this.currentSlide === this.newArrivals.length - 1) ? 0 : this.currentSlide + 1;
  }

  // --- Logic สำหรับ High Rated Scroll ---
  scrollList(offset: number) {
    this.cardList.nativeElement.scrollBy({ left: offset, behavior: 'smooth' });
  }
}