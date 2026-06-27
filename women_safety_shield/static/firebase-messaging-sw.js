

importScripts("https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-compat.js");

firebase.initializeApp({
  apiKey: "AIzaSyDpVOcSegbWr5t1ikzwbwaqr9zkgxXmZrM",
  authDomain: "woman-safety-shield.firebaseapp.com",
  projectId: "woman-safety-shield",
  messagingSenderId: "759536526665",
  appId: "1:759536526665:web:c463891a1bc5a4eca06698"
});

const messaging = firebase.messaging();