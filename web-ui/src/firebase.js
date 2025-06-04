import { initializeApp } from "firebase/app";
import { getStorage, connectStorageEmulator } from "firebase/storage";
import { getFirestore, connectFirestoreEmulator } from "firebase/firestore";
import { getFunctions, connectFunctionsEmulator } from "firebase/functions";
import { useState, useEffect } from "react";

// Firebaseの設定
// 注意: 本番環境では環境変数を使用することをお勧めします
const firebaseConfig = {
  apiKey: "AIzaSyDpHVi0IIOURj4h5BKnZi-MKp7PuyRwHUg",
  authDomain: "wedding-photo-contest-dev-032.firebaseapp.com",
  projectId: "wedding-photo-contest-dev-032",
  storageBucket: "wedding-photo-contest-dev-032.appspot.com",
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
    connectFirestoreEmulator(db, 'localhost', 8080);
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

const [firebaseInitialized, setFirebaseInitialized] = useState(false);

useEffect(() => {
  try {
    if (storage && db) {
      console.log("Firebase Storage と Firestore が正常に初期化されました");
      setFirebaseInitialized(true);
    } else {
      console.error("Firebase サービスの初期化に失敗しました");
    }
  } catch (error) {
    console.error("Firebase初期化エラー:", error);
  }
}, []);

if (!firebaseInitialized) {
  console.error("Firebase が初期化されていません");
  setAlert({
    open: true,
    message: 'Firebaseの初期化に失敗しています。システム管理者にお問い合わせください。',
    severity: 'error'
  });
  return;
}

// アップロードタスク作成前
console.log("ストレージ参照を作成:", storageRef);
console.log("アップロードタスクを開始:", file.name, file.size, "bytes");

// 進捗監視内
console.log(`アップロード進捗: ${progress}%`);

// 完了コールバック内
console.log("アップロード完了。ダウンロードURLを取得中...");
console.log("Firestoreにデータを保存中...");
console.log("処理完了、フォームをリセット"); 