import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

interface Booking {
  id: number;
  visitor_name: string;
  visitor_email: string;
  visitor_phone: string;
  booking_area: string;
  booking_date: string;
  booking_time: string;
  booking_duration: number;
  booking_purpose: string;
  created_at: string;
  status: 'pending' | 'confirmed' | 'cancelled';
}

@Component({
  selector: 'app-booking',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './booking.component.html',
  styleUrls: ['./booking.component.scss']
})
export class BookingComponent implements OnInit {
  bookings: Booking[] = [];
  filteredBookings: Booking[] = [];
  isLoading = false;
  errorMessage = '';
  
  // Filtri
  selectedArea = '';
  selectedStatus = '';
  selectedDate = '';

  // Opzioni per i filtri
  areas = [
    'Laboratorio Materiali Compositi',
    'Sala Riunioni A',
    'Sala Riunioni B',
    'Laboratorio VR/AR',
    'Ufficio Design',
    'Spazio Coworking'
  ];

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.loadBookings();
  }

  async loadBookings() {
  this.isLoading = true;
  this.errorMessage = '';
  
  try {
    console.log('🔄 Chiamando API...'); // Debug
    const response = await this.http.get<any>('http://localhost:3000/api/bookings').toPromise();
    console.log('✅ Risposta API completa:', response); // Debug
    
    // Il server restituisce { success: true, data: [...] }
    // Quindi dobbiamo prendere response.data, non response direttamente
    if (response && response.success && response.data) {
      this.bookings = response.data;
      console.log('📊 Prenotazioni caricate:', this.bookings); // Debug
    } else {
      console.log('⚠️ Nessuna prenotazione trovata');
      this.bookings = [];
    }
    
    this.filteredBookings = [...this.bookings];
    
  } catch (error) {
    console.error('❌ Errore API:', error); // Debug
    this.errorMessage = 'Errore nel caricamento delle prenotazioni dal database';
    
    // Dati di esempio per fallback
    this.bookings = [
      {
        id: 1,
        visitor_name: 'Mario Rossi',
        visitor_email: 'mario.rossi@email.com',
        visitor_phone: '+39 123 456 7890',
        booking_area: 'Laboratorio Materiali Compositi',
        booking_date: '2025-07-25',
        booking_time: '10:00',
        booking_duration: 120,
        booking_purpose: 'Test di resistenza materiali per progetto automotive nel settore dei trasporti',
        created_at: '2025-07-23T10:00:00Z',
        status: 'confirmed'
      }
      // ... altri dati esempio
    ];
    this.filteredBookings = [...this.bookings];
  } finally {
    this.isLoading = false;
  }
}

  applyFilters() {
    this.filteredBookings = this.bookings.filter(booking => {
      const areaMatch = !this.selectedArea || booking.booking_area === this.selectedArea;
      const statusMatch = !this.selectedStatus || booking.status === this.selectedStatus;
      const dateMatch = !this.selectedDate || booking.booking_date === this.selectedDate;
      
      return areaMatch && statusMatch && dateMatch;
    });
  }

  clearFilters() {
    this.selectedArea = '';
    this.selectedStatus = '';
    this.selectedDate = '';
    this.filteredBookings = [...this.bookings];
  }

  refreshData() {
    this.loadBookings();
  }

  getStatusClass(status: string): string {
    switch (status) {
      case 'confirmed': return 'status-confirmed';
      case 'cancelled': return 'status-cancelled';
      default: return 'status-pending';
    }
  }

  getStatusLabel(status: string): string {
    switch (status) {
      case 'confirmed': return 'Confermata';
      case 'cancelled': return 'Annullata';
      default: return 'In Attesa';
    }
  }

  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('it-IT', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }

  formatDateTime(dateString: string): string {
    return new Date(dateString).toLocaleString('it-IT', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  formatDuration(minutes: number): string {
    if (minutes < 60) {
      return `${minutes} minuti`;
    } else {
      const hours = Math.floor(minutes / 60);
      const remainingMinutes = minutes % 60;
      if (remainingMinutes === 0) {
        return `${hours} ${hours === 1 ? 'ora' : 'ore'}`;
      } else {
        return `${hours}h ${remainingMinutes}m`;
      }
    }
  }

  calculateEndTime(startTime: string, duration: number): string {
    const [hours, minutes] = startTime.split(':').map(Number);
    const startDate = new Date();
    startDate.setHours(hours, minutes, 0, 0);
    
    const endDate = new Date(startDate.getTime() + duration * 60000);
    
    return endDate.toTimeString().slice(0, 5);
  }

  getBookingsByStatus() {
    return {
      pending: this.bookings.filter(b => b.status === 'pending').length,
      confirmed: this.bookings.filter(b => b.status === 'confirmed').length,
      cancelled: this.bookings.filter(b => b.status === 'cancelled').length
    };
  }

  getTodayBookings(): Booking[] {
    const today = new Date().toISOString().split('T')[0];
    return this.bookings.filter(b => b.booking_date === today);
  }

  getUpcomingBookings(): Booking[] {
    const today = new Date().toISOString().split('T')[0];
    return this.bookings
      .filter(b => b.booking_date > today && b.status !== 'cancelled')
      .sort((a, b) => new Date(a.booking_date + 'T' + a.booking_time).getTime() - 
                     new Date(b.booking_date + 'T' + b.booking_time).getTime())
      .slice(0, 5);
  }
}