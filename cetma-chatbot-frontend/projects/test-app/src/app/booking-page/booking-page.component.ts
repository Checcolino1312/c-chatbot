import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { BookingComponent } from '../booking/booking.component';

@Component({
  selector: 'app-booking-page',
  standalone: true,
  imports: [CommonModule, RouterModule, BookingComponent],
  templateUrl: './booking-page.component.html',
  styleUrls: ['./booking-page.component.scss']
})
export class BookingPageComponent { }