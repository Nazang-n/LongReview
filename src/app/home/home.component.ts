import { Component, ElementRef, ViewChild, OnInit, OnDestroy, Inject, PLATFORM_ID } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FooterComponent } from '../shared/footer.component';
import { GameService } from '../services/game.service';
import { TagService } from '../services/tag.service';

// Import PrimeNG modules
import { ButtonModule } from 'primeng/button';
import { SkeletonModule } from 'primeng/skeleton';
import { CarouselModule } from 'primeng/carousel';

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
  reviewType: 'positive' | 'negative' | 'mixed' | undefined;
  isNew?: boolean;
  genresTh?: string[];
  sentimentPercent?: number;
  reviewScoreDesc?: string;
  priceThb?: string;
}

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule,
    RouterLink,
    FooterComponent,
    ButtonModule,
    SkeletonModule,
    CarouselModule
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
  @ViewChild('categoryGameList') categoryGameList!: ElementRef;

  constructor(
    @Inject(PLATFORM_ID) private platformId: Object,
    private gameService: GameService,
    private tagService: TagService
  ) { }

  // --- Logic สำหรับเกมเด็ดประจำปี ---
  years: number[] = [];
  selectedYear: number = new Date().getFullYear();
  isLoadingPositive = true;

  ngOnInit() {
    this.initYears();
    this.startAutoSlide();
    this.loadData();
    this.loadCategories();
  }

  initYears() {
    const currentYear = new Date().getFullYear();
    // Generate last 5 years
    for (let i = 0; i < 5; i++) {
      this.years.push(currentYear - i);
    }
  }

  selectYear(year: number) {
    this.selectedYear = year;
    this.loadPositiveGames();

    // Reset scroll position to start (Force immediate jump)
    if (this.cardList2 && this.cardList2.nativeElement) {
      setTimeout(() => {
        this.cardList2.nativeElement.scrollTo({ left: 0, behavior: 'auto' });
      }, 0);
    }
  }

  loadPositiveGames() {
    this.isLoadingPositive = true;
    this.positiveGames = []; // Clear list while loading (optional, or keep old data)

    // Get Popular + Specific Year (Sorted by Reviews DESC -> Positive % DESC, with "Positive" label filter)
    this.gameService.getGames(0, 10, [], 'popular', undefined, this.selectedYear).subscribe({
      next: (games: any[]) => {
        this.positiveGames = this.mapGames(games);
        this.loadGameSentiments(this.positiveGames);
        this.isLoadingPositive = false;
      },
      error: (err) => {
        console.error('Error loading positive games', err);
        this.isLoadingPositive = false;
      }
    });
  }

  loadData() {
    this.isLoading = true;

    // 1. Get New Arrivals (Top 10 Newest)
    this.gameService.getGames(0, 10, [], 'newest').subscribe({
      next: (games: any[]) => {
        this.newArrivals = this.mapGames(games);
        // Mark isNew = true for slider logic if needed
        this.newArrivals.forEach(g => g.isNew = true);
        this.loadGameSentiments(this.newArrivals);
      },
      error: (err) => console.error('Error loading new arrivals', err)
    });

    // 2. Get Popular Games (Top 10 Popular) - Sort by Total Reviews
    this.gameService.getGames(0, 10, [], 'popular_hero').subscribe({
      next: (games: any[]) => {
        this.popularGames = this.mapGames(games);
        this.isLoading = false;
        this.loadGameSentiments(this.popularGames);
      },
      error: (err) => console.error('Error loading popular games', err)
    });

    // 3. Get Positive Games (Default to current year)
    this.loadPositiveGames();
  }

  loadGameSentiments(games: Game[]) {
    const gameIds = games.map(g => g.id);
    if (gameIds.length === 0) return;

    this.gameService.getBatchSentiment(gameIds).subscribe({
      next: (sentiments) => {
        games.forEach(game => {
          const sentiment = sentiments[game.id];
          if (sentiment && sentiment.review_score_desc) {
            const desc = sentiment.review_score_desc.toLowerCase();

            // Store percentage and description for display
            game.sentimentPercent = sentiment.positive_percent;
            game.reviewScoreDesc = sentiment.review_score_desc;

            // Positive reviews
            if (desc.includes('positive') || desc.includes('very positive') || desc.includes('overwhelmingly positive')) {
              game.reviewType = 'positive';
            }
            // Mixed reviews
            else if (desc.includes('mixed')) {
              game.reviewType = 'mixed';
            }
            // Negative reviews
            else if (desc.includes('negative')) {
              game.reviewType = 'negative';
              game.sentimentPercent = sentiment.negative_percent;
            }
            // No reviews or unknown
            else {
              game.reviewType = undefined;
            }
          }
        });
      }
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
        reviewTags: [],
        image: game.image_url || 'https://via.placeholder.com/460x215',
        rating: game.rating,
        tags: [],
        reviewType: undefined, // Will be updated by loadGameSentiments
        isNew: false,
        priceThb: game.price_thb
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

  // --- Logic สำหรับ Top 10 Categories ---
  categories: any[] = [];
  selectedCategory: number | null = null;
  categoryGames: Game[] = [];
  isLoadingCategories = true;
  isLoadingCategoryGames = false;

  categoryResponsiveOptions = [
    {
      breakpoint: '1024px',
      numVisible: 5,
      numScroll: 3
    },
    {
      breakpoint: '768px',
      numVisible: 3,
      numScroll: 2
    },
    {
      breakpoint: '560px',
      numVisible: 2,
      numScroll: 1
    }
  ];

  loadCategories() {
    this.isLoadingCategories = true;
    this.tagService.getTagStats().subscribe({
      next: (res) => {
        if (res.success && res.stats.genres) {
          // Filter out unwanted genres (same as Game List)
          const filteredGenres = res.stats.genres.filter(
            (genre: any) => genre.name !== 'Massively Multiplayer' && genre.name !== 'Early Access'
          );

          // Sort by game count
          this.categories = filteredGenres.sort((a: any, b: any) => b.game_count - a.game_count);

          // Select first category by default if available
          if (this.categories.length > 0) {
            this.selectCategory(this.categories[0].id);
          }
        }
        this.isLoadingCategories = false;
      },
      error: (err) => {
        console.error('Error loading categories', err);
        this.isLoadingCategories = false;
      }
    });
  }

  selectCategory(categoryId: number) {
    this.selectedCategory = categoryId;
    this.loadCategoryGames();
  }

  loadCategoryGames() {
    if (!this.selectedCategory) return;

    this.isLoadingCategoryGames = true;
    this.categoryGames = []; // Clear current list

    // Fetch top 10 games for this category, sorted by popularity (Total Reviews)
    this.gameService.getGames(0, 10, [this.selectedCategory], 'popular').subscribe({
      next: (games: any[]) => {
        this.categoryGames = this.mapGames(games);

        // Reorder tags: Put the current category tag FIRST so it's always visible
        const currentCategory = this.categories.find(c => c.id === this.selectedCategory);
        if (currentCategory && currentCategory.name_th) {
          const categoryNameTh = currentCategory.name_th;
          this.categoryGames.forEach(game => {
            if (game.genresTh && game.genresTh.includes(categoryNameTh)) {
              // Remove existing occurrence and unshift to front
              game.genresTh = [
                categoryNameTh,
                ...game.genresTh.filter(g => g !== categoryNameTh)
              ];
            }
          });
        }

        this.isLoadingCategoryGames = false;
        this.loadGameSentiments(this.categoryGames);

        // Reset scroll position after view updates
        setTimeout(() => {
          if (this.categoryGameList) {
            this.categoryGameList.nativeElement.scrollLeft = 0;
          }
        }, 0);
      },
      error: (err) => {
        console.error('Error loading category games', err);
        this.isLoadingCategoryGames = false;
      }
    });
  }

  // --- Logic สำหรับ High Rated Scroll ---
  scrollList(offset: number) {
    this.cardList.nativeElement.scrollBy({ left: offset, behavior: 'smooth' });
  }

  scrollList2(offset: number) {
    this.cardList2.nativeElement.scrollBy({ left: offset, behavior: 'smooth' });
  }

  scrollCategoryGames(offset: number) {
    if (this.categoryGameList) {
      this.categoryGameList.nativeElement.scrollBy({ left: offset, behavior: 'smooth' });
    }
  }
}