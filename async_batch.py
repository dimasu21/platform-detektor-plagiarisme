import os
import json
import logging
from werkzeug.datastructures import FileStorage

logger = logging.getLogger(__name__)

def process_batch_async(batch_id, file_paths, original_filenames, current_user_id, app_context):
    with app_context:
        status_file = os.path.join('static', 'uploads', 'batch_results', f'{batch_id}_status.json')
        
        def update_status(status, progress, message, error=None, is_complete=False):
            data = {
                'status': status,
                'progress': progress,
                'message': message,
                'error': error,
                'is_complete': is_complete
            }
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)
                
        try:
            from file_parser import extract_text_and_images_from_file
            from batch_comparison import compare_all_pairs
            
            documents = []
            errors = []
            total_files = len(file_paths)
            
            for idx, (path, original_name) in enumerate(zip(file_paths, original_filenames)):
                update_status('processing', int((idx / total_files) * 50), f"Memproses gambar {idx+1} dari {total_files}...")
                
                try:
                    ext = original_name.rsplit('.', 1)[1].lower() if '.' in original_name else ''
                    
                    if ext in ['png', 'jpg', 'jpeg']:
                        # For images, open directly with PIL and run the OCR pipeline
                        from PIL import Image
                        image = Image.open(path)
                        original_image = image.copy()
                        
                        from file_parser import _advanced_preprocess_for_handwriting, _multi_pass_ocr, _clean_ocr_text
                        
                        clean_document = _advanced_preprocess_for_handwriting(image)
                        raw_text = _multi_pass_ocr(clean_document, lang='ind+eng')
                        clean_text = _clean_ocr_text(raw_text)
                        
                        if clean_text:
                            # Save original image for highlighting
                            img_filename = f'batch_{batch_id}_{idx}_0.png'
                            img_path = os.path.join('static', 'uploads', img_filename)
                            os.makedirs(os.path.dirname(img_path), exist_ok=True)
                            original_image.save(img_path, 'PNG')
                            
                            documents.append({
                                'name': original_name,
                                'text': clean_text,
                                'images': [f'uploads/{img_filename}']
                            })
                        else:
                            err_msg = f"Filter dropped all text. Raw: {raw_text[:80]}..." if raw_text else "Tesseract OCR found 0 words."
                            errors.append({'filename': original_name, 'error': err_msg})
                            logger.error(f"OCR failed for {original_name}: {err_msg}")
                    else:
                        # For non-image files (pdf, docx, txt), use the original FileStorage approach
                        with open(path, 'rb') as f_in:
                            mock_f = FileStorage(stream=f_in, filename=original_name)
                            data = extract_text_and_images_from_file(mock_f)
                            
                            if data.get('error'):
                                errors.append({'filename': original_name, 'error': data['error']})
                            elif data and data.get('text'):
                                image_paths = []
                                if data.get('images'):
                                    for img_idx, img in enumerate(data['images']):
                                        img_fn = f'batch_{batch_id}_{idx}_{img_idx}.png'
                                        img_p = os.path.join('static', 'uploads', img_fn)
                                        os.makedirs(os.path.dirname(img_p), exist_ok=True)
                                        img.save(img_p, 'PNG')
                                        image_paths.append(f'uploads/{img_fn}')
                                
                                documents.append({
                                    'name': original_name,
                                    'text': data['text'],
                                    'images': image_paths
                                })
                            else:
                                errors.append({'filename': original_name, 'error': 'Could not extract text'})
                except Exception as e:
                    logger.error(f"Error processing {original_name}: {e}", exc_info=True)
                    errors.append({'filename': original_name, 'error': f'{type(e).__name__}: {str(e)}'})
            
            if len(documents) < 2:
                update_status('error', 100, "Gagal memproses gambar.", "Need at least 2 valid documents with extractable text.", True)
                return
                
            update_status('processing', 60, "Membandingkan kemiripan dokumen...")
            results = compare_all_pairs(documents)
            results['errors'] = errors
            
            update_status('processing', 80, "Menyimpan hasil perbandingan...")
            batch_results_dir = os.path.join('static', 'uploads', 'batch_results')
            os.makedirs(batch_results_dir, exist_ok=True)
            batch_file_path = os.path.join(batch_results_dir, f'{batch_id}.json')
            with open(batch_file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f)
                
            # Record Scan History
            if current_user_id:
                try:
                    from app import db, ScanHistory
                    max_score = 0.0
                    if results['pairs']:
                        max_score = float(max([p['similarity'] for p in results['pairs']]))
                        
                    status_text = 'Aman'
                    if max_score >= 90:
                        status_text = 'Plagiat'
                    elif max_score >= 60:
                        status_text = 'Warning'
                        
                    new_scan = ScanHistory(
                        user_id=current_user_id,
                        suspect_filename=f"Batch: {len(documents)} docs",
                        method='Batch Check',
                        score=max_score,
                        status=status_text
                    )
                    db.session.add(new_scan)
                    db.session.commit()
                except Exception as e:
                    logger.error(f"Failed to record history: {e}")
                    
            update_status('completed', 100, "Selesai!", None, True)
            
        except Exception as e:
            logger.error(f"Async processing error: {e}", exc_info=True)
            update_status('error', 100, "Terjadi kesalahan internal.", str(e), True)
        finally:
            # Clean up temp files
            for path in file_paths:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except:
                    pass
