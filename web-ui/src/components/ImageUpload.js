import React, { useState } from 'react';
import { 
  Box, 
  Button, 
  TextField, 
  Typography, 
  Paper, 
  CircularProgress,
  Alert,
  Snackbar,
  Tooltip,
  IconButton
} from '@mui/material';
import { ref, uploadBytesResumable, getDownloadURL } from 'firebase/storage';
import { collection, addDoc, serverTimestamp } from 'firebase/firestore';
import { storage, db } from '../firebase';
import { v4 as uuidv4 } from 'uuid';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';

const ImageUpload = () => {
  const [userName, setUserName] = useState('');
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [alert, setAlert] = useState({ open: false, message: '', severity: 'info' });

  // ファイル選択時の処理
  const handleFileChange = (e) => {
    if (e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);

      // プレビューを表示
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result);
      };
      reader.readAsDataURL(selectedFile);
    }
  };

  // フォーム送信処理
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // 入力検証
    if (!userName.trim()) {
      setAlert({
        open: true,
        message: 'お名前を入力してください',
        severity: 'error'
      });
      return;
    }

    if (!file) {
      setAlert({
        open: true,
        message: '画像を選択してください',
        severity: 'error'
      });
      return;
    }

    // 画像の拡張子チェック
    const fileExtension = file.name.split('.').pop().toLowerCase();
    if (!['jpg', 'jpeg', 'png'].includes(fileExtension)) {
      setAlert({
        open: true,
        message: 'JPGまたはPNG形式の画像を選択してください',
        severity: 'error'
      });
      return;
    }

    // アップロード開始
    setUploading(true);
    setUploadProgress(0);

    try {
      // 一意のファイル名を生成
      const fileName = `${uuidv4()}.${fileExtension}`;
      const storageRef = ref(storage, `wedding-photos/${fileName}`);

      // アップロードタスクを作成
      const uploadTask = uploadBytesResumable(storageRef, file);

      // アップロードの進捗監視
      uploadTask.on(
        'state_changed',
        (snapshot) => {
          const progress = Math.round(
            (snapshot.bytesTransferred / snapshot.totalBytes) * 100
          );
          setUploadProgress(progress);
        },
        (error) => {
          console.error('アップロードエラー:', error);
          setAlert({
            open: true,
            message: 'アップロード中にエラーが発生しました',
            severity: 'error'
          });
          setUploading(false);
        },
        async () => {
          // アップロード完了
          const downloadURL = await getDownloadURL(uploadTask.snapshot.ref);
          
          // Firestoreにメタデータを保存
          await addDoc(collection(db, 'photos'), {
            userName: userName,
            photoUrl: downloadURL,
            fileName: fileName,
            timestamp: serverTimestamp(),
            score: 0, // スコアは初期値0、Cloud Functionsで計算後に更新される
            faceCount: 0,
            processed: false // 処理状態のフラグ
          });

          // フォームをリセット
          setUserName('');
          setFile(null);
          setPreview('');
          setUploading(false);
          
          // 成功メッセージ
          setAlert({
            open: true,
            message: '写真が正常にアップロードされました！分析結果をお待ちください。複数のターゲットに対する類似度スコアが計算されます。',
            severity: 'success'
          });
        }
      );
    } catch (error) {
      console.error('エラー:', error);
      setAlert({
        open: true,
        message: 'エラーが発生しました。後でもう一度お試しください。',
        severity: 'error'
      });
      setUploading(false);
    }
  };

  return (
    <Paper className="form-container" elevation={3}>
      <Typography variant="h4" component="h1" gutterBottom align="center">
        写真をアップロード
      </Typography>
      
      <Box sx={{ textAlign: 'center', mb: 3 }}>
        <Typography variant="body1" color="text.secondary">
          画像をアップロードして、顔認識コンテストにご参加ください
          <Tooltip title="アップロードされた画像は複数のターゲットに対して類似度が計算されます。結果はランキングページで確認できます。" arrow>
            <IconButton size="small" sx={{ ml: 0.5 }}>
              <HelpOutlineIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Typography>
      </Box>
      
      <Box component="form" onSubmit={handleSubmit} noValidate sx={{ mt: 3 }}>
        <TextField
          margin="normal"
          required
          fullWidth
          id="userName"
          label="お名前"
          name="userName"
          value={userName}
          onChange={(e) => setUserName(e.target.value)}
          disabled={uploading}
          sx={{ mb: 3 }}
        />
        
        <Box sx={{ mb: 3 }}>
          <input
            accept="image/*"
            style={{ display: 'none' }}
            id="photo-upload"
            type="file"
            onChange={handleFileChange}
            disabled={uploading}
          />
          <label htmlFor="photo-upload">
            <Button
              variant="contained"
              component="span"
              color="primary"
              fullWidth
              disabled={uploading}
            >
              写真を選択
            </Button>
          </label>
          {file && (
            <Typography variant="body2" sx={{ mt: 1 }}>
              選択ファイル: {file.name}
            </Typography>
          )}
        </Box>
        
        {preview && (
          <Box sx={{ mb: 3, textAlign: 'center' }}>
            <img src={preview} alt="プレビュー" className="image-preview" />
          </Box>
        )}
        
        <Button
          type="submit"
          fullWidth
          variant="contained"
          color="secondary"
          disabled={uploading || !file || !userName.trim()}
          sx={{ mb: 2 }}
        >
          {uploading ? (
            <>
              アップロード中... {uploadProgress}%
              <CircularProgress size={24} sx={{ ml: 1, color: 'white' }} />
            </>
          ) : (
            '送信'
          )}
        </Button>
      </Box>
      
      <Snackbar
        open={alert.open}
        autoHideDuration={6000}
        onClose={() => setAlert({ ...alert, open: false })}
      >
        <Alert 
          onClose={() => setAlert({ ...alert, open: false })} 
          severity={alert.severity}
          sx={{ width: '100%' }}
        >
          {alert.message}
        </Alert>
      </Snackbar>
    </Paper>
  );
};

export default ImageUpload; 