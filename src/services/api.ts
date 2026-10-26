/**
 * ManiPool Shared Backend API Client
 *
 * Implements backend integration service for Sumukh's backend:
 * - Student authentication (MAHE email, OTP verification, demo logins, JWT sessions)
 * - Ride request operations (create, search, cancel, rematch)
 * - Real matching queries
 * - Carpool group operations (create, independent accept, decline, pickup mode, delays, bookings, start, complete, leave)
 * - Persistent group chat & message recovery
 * - Notifications & device push token registration
 * - Safety & issue report handling
 */

import { Platform } from 'react-native';

const DEFAULT_BASE_URL =
  Platform.OS === 'android'
    ? 'http://10.0.2.2:8000/api'
    : 'http://localhost:8000/api';

export class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl = DEFAULT_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  setToken(token: string | null) {
    this.token = token;
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
  ): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorMessage = `HTTP error ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          errorMessage = typeof errorData.detail === 'string'
            ? errorData.detail
            : JSON.stringify(errorData.detail);
        }
      } catch {
        // Fallback to response status text
        if (response.statusText) {
          errorMessage = response.statusText;
        }
      }
      throw new Error(errorMessage);
    }

    return response.json() as Promise<T>;
  }

  // Auth endpoints
  async demoLogin(name: string, email: string, area = 'MAHE Campus') {
    const data = await this.request<{
      access_token: string;
      user: { id: string; name: string; email: string; area: string };
    }>('/auth/demo-login', {
      method: 'POST',
      body: JSON.stringify({ name, email, area }),
    });
    this.setToken(data.access_token);
    return data;
  }

  async requestOtp(email: string) {
    return this.request<{ message: string; dev_otp_code?: string }>(
      '/auth/request-otp',
      {
        method: 'POST',
        body: JSON.stringify({ email }),
      },
    );
  }

  async verifyOtp(email: string, code: string) {
    const data = await this.request<{
      access_token: string;
      user: { id: string; name: string; email: string; area: string };
    }>('/auth/verify-otp', {
      method: 'POST',
      body: JSON.stringify({ email, code }),
    });
    this.setToken(data.access_token);
    return data;
  }

  async getMe() {
    return this.request<{
      id: string;
      name: string;
      email: string;
      area: string;
      is_verified: boolean;
      role: string;
    }>('/auth/me');
  }

  // Ride Requests
  async createRideRequest(payload: {
    pickup_id: string;
    destination_id: string;
    departure: string;
    flexibility: number;
  }) {
    return this.request<any>('/requests', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async listMyRequests() {
    return this.request<any[]>('/requests');
  }

  async getRequest(id: string) {
    return this.request<any>(`/requests/${id}`);
  }

  async cancelRequest(id: string) {
    return this.request<{ message: string; request_id: string }>(
      `/requests/${id}`,
      {
        method: 'DELETE',
      },
    );
  }

  // Matching
  async getMatches(requestId: string) {
    return this.request<any[]>(`/matching/${requestId}`);
  }

  // Carpool Groups
  async createGroup(payload: {
    candidate_request_ids: string[];
    pickup_mode?: 'common' | 'sequential';
    vehicle_type?: 'cab' | 'auto';
  }) {
    return this.request<any>('/groups', {
      method: 'POST',
      body: JSON.stringify({
        pickup_mode: 'common',
        vehicle_type: 'cab',
        ...payload,
      }),
    });
  }

  async getGroup(groupId: string) {
    return this.request<any>(`/groups/${groupId}`);
  }

  async acceptGroup(groupId: string) {
    return this.request<any>(`/groups/${groupId}/accept`, {
      method: 'POST',
    });
  }

  async declineGroup(groupId: string) {
    return this.request<{ message: string }>(`/groups/${groupId}/decline`, {
      method: 'POST',
    });
  }

  async updatePickupMode(
    groupId: string,
    mode: 'common' | 'sequential',
    meetingPointId?: string,
  ) {
    return this.request<any>(`/groups/${groupId}/pickup-mode`, {
      method: 'POST',
      body: JSON.stringify({ mode, meeting_point_id: meetingPointId }),
    });
  }

  async delayDeparture(groupId: string, minutes = 10) {
    return this.request<any>(`/groups/${groupId}/delay`, {
      method: 'POST',
      body: JSON.stringify({ minutes }),
    });
  }

  async bookRide(
    groupId: string,
    vehicleType: 'cab' | 'auto',
    farePaise?: number,
  ) {
    return this.request<any>(`/groups/${groupId}/book`, {
      method: 'POST',
      body: JSON.stringify({ vehicle_type: vehicleType, fare_paise: farePaise }),
    });
  }

  async startRide(groupId: string) {
    return this.request<any>(`/groups/${groupId}/start`, {
      method: 'POST',
    });
  }

  async completeRide(groupId: string) {
    return this.request<any>(`/groups/${groupId}/complete`, {
      method: 'POST',
    });
  }

  async leaveGroup(groupId: string, reason?: string) {
    return this.request<{ message: string; remaining_members_count: number }>(
      `/groups/${groupId}/leave`,
      {
        method: 'POST',
        body: JSON.stringify({ reason }),
      },
    );
  }

  // Chat
  async listMessages(groupId: string, since?: string) {
    const query = since ? `?since=${encodeURIComponent(since)}` : '';
    return this.request<any[]>(`/groups/${groupId}/messages${query}`);
  }

  async sendMessage(groupId: string, text: string) {
    return this.request<any>(`/groups/${groupId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ text }),
    });
  }

  // Notifications
  async listNotifications() {
    return this.request<any[]>('/notifications');
  }

  async registerDeviceToken(token: string, platform = 'android') {
    return this.request<{ message: string }>('/notifications/register-device', {
      method: 'POST',
      body: JSON.stringify({ token, platform }),
    });
  }

  // Reports
  async submitReport(payload: {
    text: string;
    category?: string;
    ride_id?: string;
    group_id?: string;
  }) {
    return this.request<any>('/reports', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async listMyReports() {
    return this.request<any[]>('/reports');
  }
}

export const api = new ApiClient();
