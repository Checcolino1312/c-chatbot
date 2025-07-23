import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Booking {
  id: number;
  visitor_name: string;
  visitor_email: string;
  visitor_phone: string;
  booking_area: string;
  booking_date: string;
  booking_time: string;
  booking_duration: string;
  booking_purpose: string;
  created_at: string;
  status: 'pending' | 'confirmed' | 'cancelled';
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

@Injectable({
  providedIn: 'root'
})
export class BookingService {
  private readonly apiUrl = 'http://localhost:3000/api/bookings';

  constructor(private http: HttpClient) {}

  // READ - Ottieni tutte le prenotazioni (già esistente)
  getAllBookings(): Observable<ApiResponse<Booking[]>> {
    return this.http.get<ApiResponse<Booking[]>>(`${this.apiUrl}`);
  }

  // UPDATE - Aggiorna una prenotazione completa
  updateBooking(id: number, booking: Partial<Booking>): Observable<ApiResponse<Booking>> {
    return this.http.put<ApiResponse<Booking>>(`${this.apiUrl}/${id}`, booking);
  }

  // UPDATE STATUS - Aggiorna solo lo status
  updateBookingStatus(id: number, status: Booking['status']): Observable<ApiResponse<Booking>> {
    return this.http.patch<ApiResponse<Booking>>(`${this.apiUrl}/${id}/status`, { status });
  }

  // DELETE - Elimina una prenotazione
  deleteBooking(id: number): Observable<ApiResponse<void>> {
    return this.http.delete<ApiResponse<void>>(`${this.apiUrl}/${id}`);
  }

  // Validazione form
  validateBooking(booking: Partial<Booking>): string[] {
    const errors: string[] = [];

    if (!booking.visitor_name?.trim()) {
      errors.push('Nome visitatore è obbligatorio');
    }

    if (!booking.visitor_email?.trim()) {
      errors.push('Email è obbligatoria');
    } else if (!this.isValidEmail(booking.visitor_email)) {
      errors.push('Email non valida');
    }

    if (!booking.visitor_phone?.trim()) {
      errors.push('Telefono è obbligatorio');
    }

    if (!booking.booking_area?.trim()) {
      errors.push('Area/Laboratorio è obbligatorio');
    }

    if (!booking.booking_date?.trim()) {
      errors.push('Data è obbligatoria');
    }

    if (!booking.booking_time?.trim()) {
      errors.push('Orario è obbligatorio');
    }

    if (!booking.booking_duration?.trim()) {
      errors.push('Durata è obbligatoria');
    }

    if (!booking.booking_purpose?.trim()) {
      errors.push('Scopo della prenotazione è obbligatorio');
    }

    return errors;
  }

  private isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }
}