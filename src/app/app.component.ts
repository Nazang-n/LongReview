import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  standalone: false,
  styleUrl: './app.component.css'
})
export class AppComponent implements OnInit {
  title = 'LongReview';
  private readonly BACKEND_URL = 'https://longreview.onrender.com';
  private readonly PING_INTERVAL = 5 * 60 * 1000; // 5 minutes

  constructor(private http: HttpClient) { }

  ngOnInit(): void {
    // Keep backend alive by pinging every 5 minutes
    setInterval(() => {
      this.http.get(`${this.BACKEND_URL}/health`).subscribe({
        error: () => { } // Silently ignore errors
      });
    }, this.PING_INTERVAL);
  }
}
