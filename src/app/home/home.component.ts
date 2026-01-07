import { Component, ElementRef, ViewChild, OnInit, OnDestroy, Inject, PLATFORM_ID } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { RouterLink } from '@angular/router';
import { HeaderComponent } from '../shared/header.component';
import { FooterComponent } from '../shared/footer.component';
import { GameService } from '../services/game.service';
import { TagService } from '../services/tag.service';

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
  genresTh?: string[];
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
  isLoading = true;

  newArrivals: Game[] = []; // Top 10 New
  popularGames: Game[] = []; // Top 10 Popular
  positiveGames: Game[] = []; // Positive Reviews (Placeholder for now, using popular)

  @ViewChild('cardList') cardList!: ElementRef;
  @ViewChild('cardList2') cardList2!: ElementRef;

  constructor(
    @Inject(PLATFORM_ID) private platformId: Object,
    private gameService: GameService,
    private tagService: TagService
  ) { }

  ngOnInit() {
    this.startAutoSlide();
    this.loadData();
  }

  loadData() {
    this.isLoading = true;

    // 1. Get New Arrivals (Top 10 Newest)
    this.gameService.getGames(0, 10, [], 'newest').subscribe({
      next: (games: any[]) => {
        this.newArrivals = this.mapGames(games);
        // Mark isNew = true for slider logic if needed
        this.newArrivals.forEach(g => g.isNew = true);
      },
      error: (err) => console.error('Error loading new arrivals', err)
    });

    // 2. Get Popular Games (Top 10 Popular) - Sort by Rating
    this.gameService.getGames(0, 10, [], 'rating').subscribe({
      next: (games: any[]) => {
        this.popularGames = this.mapGames(games);
        // For now, Positive Reviews = Popular Games (High Rating)
        this.positiveGames = [...this.popularGames];
        this.isLoading = false;
      },
      error: (err) => console.error('Error loading popular games', err)
    });
  }

  mapGames(backendGames: any[]): Game[] {
    return backendGames.map(game => {
      // Parse fields using existing logic
      const genres = game.genre ? game.genre.split(',').map((g: string) => g.trim()) : [];
      const genresTh = game.genre_th ? game.genre_th.split(',').map((g: string) => g.trim()) : genres;

      return {
        id: game.id,
        title: game.title,
        description: game.about_game_th || game.description || 'No description',
        releaseDate: game.release_date || '',
        genres: genres,
        genresTh: genresTh,
        reviewTags: [], // Backend doesn't send these fully yet in list view? Or need separate call? 
        // Actually `Game` model has no reviewTags column in DB, it's computed?
        // For now leave empty, or maybe we fetch them?
        // Let's use `game.review_type` from backend
        image: game.image_url || 'https://via.placeholder.com/460x215',
        rating: game.rating,
        tags: [], // Deprecated
        reviewType: game.review_type || 'mixed', // Backend now sends this
        isNew: false
      };
    });
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
  nextSlide() {
    if (this.popularGames.length > 0) {
      this.currentSlide = (this.currentSlide + 1) % this.popularGames.length;
    }
  }

  prevSlide() {
    if (this.popularGames.length > 0) {
      this.currentSlide = (this.currentSlide - 1 + this.popularGames.length) % this.popularGames.length;
    }
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

  scrollList2(offset: number) {
    this.cardList2.nativeElement.scrollBy({ left: offset, behavior: 'smooth' });
  }
}