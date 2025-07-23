import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BookingComponent } from './booking.component';

@Component({
  selector: 'app-booking-page',
  standalone: true,
  imports: [CommonModule, BookingComponent],
  template: `
    <div class="booking-page">
      <app-booking></app-booking>
    </div>
  `,
  styles: [`
    .booking-page {
      min-height: 100vh;
      background-color: #f8f9fa;
    }
  `]
})
export class BookingPageComponent { }