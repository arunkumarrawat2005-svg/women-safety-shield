importScripts("https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-compat.js");

// Firebase Configuration
firebase.initializeApp({
  apiKey: "AIzaSyDpVOcSegbWr5t1ikzwbwaqr9zkgxXmZrM",
  authDomain: "woman-safety-shield.firebaseapp.com",
  projectId: "woman-safety-shield",
  storageBucket: "woman-safety-shield.appspot.com",
  messagingSenderId: "759536526665",
  appId: "1:759536526665:web:c463891a1bc5a4eca06698"
});

// Initialize Firebase Messaging
const messaging = firebase.messaging();

// Handle Background Notifications
messaging.onBackgroundMessage(function (payload) {
  console.log("Received background message:", payload);

  const notificationTitle =
    payload.notification?.title || "Woman Safety Shield";

  const notificationOptions = {
    body: payload.notification?.body || "You have a new notification.",
    icon: "/icon-192.png", // Agar icon nahi hai to is line ko hata do
    badge: "/badge-72.png", // Agar badge nahi hai to is line ko hata do
    data: payload.data || {}
  };

  self.registration.showNotification(
    notificationTitle,
    notificationOptions
  );
});

// Notification Click Event
self.addEventListener("notificationclick", function (event) {
  event.notification.close();

  event.waitUntil(
    clients.openWindow("/")
  );
});