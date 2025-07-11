import { initializeApp } from "firebase/app";
import { getStorage, connectStorageEmulator } from "firebase/storage";
import { getFirestore, connectFirestoreEmulator } from "firebase/firestore";
import { getFunctions, connectFunctionsEmulator } from "firebase/functions";

// Firebaseの設定
const firebaseConfig = {
  apiKey: "AIzaSyDpHVi0IIOURj4h5BKnZi-MKp7PuyRwHUg",
  authDomain: "wedding-photo-contest-dev-032.firebaseapp.com",
  projectId: "wedding-photo-contest-dev-032",
  storageBucket: "wedding-photo-contest-dev-032.firebasestorage.app",
  messagingSenderId: "105913055858",
  appId: "1:105913055858:web:c964ee5de0da2ab00e20eb",
  measurementId: "G-0PJR98BGJ8"
};

// Firebaseの初期化
const app = initializeApp(firebaseConfig);

// Firestoreの初期化
export const db = getFirestore(app);

// Cloud Storageの初期化
export const storage = getStorage(app);

// Cloud Functionsの初期化
export const functions = getFunctions(app);

// ローカル開発環境の場合、エミュレーターに接続
if (process.env.NODE_ENV === 'development') {
  try {
    // Firestoreエミュレーターに接続
    connectFirestoreEmulator(db, 'localhost', 8081);
    console.log("Firestoreエミュレーターに接続しました");
    
    // Storageエミュレーターに接続
    connectStorageEmulator(storage, 'localhost', 9199);
    console.log("Storageエミュレーターに接続しました");
    
    // Functionsエミュレーターに接続
    connectFunctionsEmulator(functions, 'localhost', 5001);
    console.log("Functionsエミュレーターに接続しました");
  } catch (error) {
    console.error("エミュレーター接続エラー:", error);
  }
}

export default app;