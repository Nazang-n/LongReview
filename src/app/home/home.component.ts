import { Component, ElementRef, ViewChild, OnInit, OnDestroy, Inject, PLATFORM_ID } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { RouterLink } from '@angular/router';
import { HeaderComponent } from '../shared/header.component';
import { FooterComponent } from '../shared/footer.component';

// Import PrimeNG modules
import { ButtonModule } from 'primeng/button';

// Interface สำหรับข้อมูลเกม
interface Game {
  id: number;
  title: string;
  description: string;
  releaseDate: string;
  genres: string[];
  reviewTags: string[];
  image: string;
  rating: number;
  tags: string[];
  reviewType: 'positive' | 'negative' | 'mixed';
  isNew?: boolean;
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
      tags: ['Action', 'Battle Royale'],
      description: '',
      releaseDate: '',
      genres: [],
      reviewTags: [],
      reviewType: 'positive'
    },
    {
      id: 2,
      title: 'Elden Ring',
      image: 'https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg',
      rating: 5.0,
      tags: ['RPG', 'Open World'],
      description: '',
      releaseDate: '',
      genres: [],
      reviewTags: [],
      reviewType: 'positive'
    },
    {
      id: 3,
      title: 'Black Myth: Wukong',
      image: 'https://cdn.akamai.steamstatic.com/steam/apps/2358720/header.jpg',
      rating: 4.8,
      tags: ['Action', 'Adventure'],
      description: '',
      releaseDate: '',
      genres: [],
      reviewTags: [],
      reviewType: 'positive'
    },
    {
      id: 4,
      title: 'Call of Duty: Black Ops 6',
      image: 'https://cdn.akamai.steamstatic.com/steam/apps/2933620/header.jpg',
      rating: 4.2,
      tags: ['FPS', 'Action'],
      description: '',
      releaseDate: '',
      genres: [],
      reviewTags: [],
      reviewType: 'positive'
    },
  ];

  // --- Data ส่วนคะแนนรีวิวสูง ---
  highRatedGames: Game[] = [
    {
      id: 101,
      title: 'Apex Legends',
      description: 'เกมที่ผสมผสาน Battle Royale ที่มีตัวละครที่แตกต่างกันความสามารถของแต่ละตัวละครที่',
      releaseDate: '4 ตุลาคม 2562',
      genres: ['Battle Royale', 'FPS'],
      reviewTags: ['ยิงปืน', 'เกมไว'],
      image: 'https://cdn.cloudflare.steamstatic.com/steam/apps/1172470/header.jpg',
      rating: 4.5,
      tags: ['ยิงปืน', 'เกมไว'],
      reviewType: 'positive',
      isNew: false
    },
    {
      id: 102,
      title: 'Elden Ring',
      description: 'เกม Action RPG โอเพ่นเวิลด์จากทีมสร้าง Dark Souls ร่วมกับ George R.R. Martin',
      releaseDate: '25 กุมภาพันธ์ 2565',
      genres: ['Action RPG', 'โอเพ่นเวิลด์'],
      reviewTags: ['ยาก', 'ท้าทาย'],
      image: 'https://image.api.playstation.com/vulcan/ap/rnd/202110/2000/aGhopp3MHppi7kooGE2Dtt8C.png',
      rating: 5.0,
      tags: ['RPG', 'Open World'],
      reviewType: 'positive',
      isNew: false
    },
    {
      id: 103,
      title: 'God of War Ragnarök',
      description: 'ภาคต่อของ God of War 2018 ที่ชวนให้ไปสำรวจนอร์ดิก',
      releaseDate: '9 พฤศจิกายน 2565',
      genres: ['Action', 'ผจญภัย'],
      reviewTags: ['เนื้อเรื่องดี', 'กราฟิกสวย'],
      image: 'https://image.api.playstation.com/vulcan/ap/rnd/202207/1210/4xJ8XB3bi888QTLZYdl7Oi0s.png',
      rating: 4.9,
      tags: ['Action', 'Story Rich'],
      reviewType: 'positive',
      isNew: false
    },
    {
      id: 104,
      title: 'Baldur\'s Gate 3',
      description: 'เกม RPG แนว D&D ที่ให้เสรีภาพในการเล่นสูงมาก',
      releaseDate: '3 สิงหาคม 2566',
      genres: ['RPG', 'กลยุทธ์'],
      reviewTags: ['เนื้อหาเยอะ', 'เล่นซ้ำได้'],
      image: 'https://cdn.cloudflare.steamstatic.com/steam/apps/1086940/header.jpg',
      rating: 4.8,
      tags: ['RPG', 'Strategy'],
      reviewType: 'positive',
      isNew: true
    },
    {
      id: 105,
      title: 'Red Dead Redemption 2',
      description: 'เกมคาวบอยโอเพ่นเวิลด์ที่มีรายละเอียดสูงมาก',
      releaseDate: '26 ตุลาคม 2561',
      genres: ['Action', 'โอเพ่นเวิลด์'],
      reviewTags: ['เนื้อเรื่องดี', 'โลกกว้าง'],
      image: 'https://cdn.cloudflare.steamstatic.com/steam/apps/1174180/header.jpg',
      rating: 4.8,
      tags: ['Action', 'Open World'],
      reviewType: 'positive',
      isNew: false
    },
    {
      id: 106,
      title: 'Spider-Man 2',
      description: 'ภาคต่อของ Spider-Man ที่ให้คุณเล่นได้ทั้ง Peter Parker และ Miles Morales',
      releaseDate: '20 ตุลาคม 2566',
      genres: ['Action', 'ผจญภัย'],
      reviewTags: ['สนุก', 'กราฟิกสวย'],
      image: 'https://image.api.playstation.com/vulcan/ap/rnd/202306/1219/1c7b75d8ed9271516546560d219ad0b22ee0a263b4537bd8.png',
      rating: 4.7,
      tags: ['Action', 'Adventure'],
      reviewType: 'positive',
      isNew: true
    }
  ];

  @ViewChild('cardList') cardList!: ElementRef;

  constructor(@Inject(PLATFORM_ID) private platformId: Object) { }

  ngOnInit() {
    this.startAutoSlide();
  }

  ngOnDestroy() {
    this.stopAutoSlide();
  }

  startAutoSlide() {
    if (isPlatformBrowser(this.platformId)) {
      this.autoSlideInterval = setInterval(() => {
        this.nextSlide();
      }, 5000);
    }
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