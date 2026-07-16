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
            total_files = len(file_paths)
            
            for idx, (path, original_name) in enumerate(zip(file_paths, original_filenames)):
                update_status('processing', int((idx / total_files) * 50), f"Memproses gambar {idx+1} dari {total_files}...")
                
                with open(path, 'rb') as f_in:
                    mock_f = FileStorage(stream=f_in, filename=original_name)
                    data = extract_text_and_images_from_file(mock_f)
                    
                    if data.get('error'):
                        logger.error(f"Error on {original_name}: {data['error']}")
                        # Still record it so we don't lose the whole batch
                    elif data and data.get('text'):
                        image_paths = []
                        if data.get('images'):
                            for img_idx, img in enumerate(data['images']):
                                img_filename = f'batch_{batch_id}_{idx}_{img_idx}.png'
                                img_path = os.path.join('static', 'uploads', img_filename)
                                os.makedirs(os.path.dirname(img_path), exist_ok=True)
                                img.save(img_path, 'PNG')
                                image_paths.append(f'uploads/{img_filename}')
                        
                        documents.append({
                            'name': original_name,
                            'text': data['text'],
                            'images': image_paths
                        })
            
            if len(documents) < 2:
                update_status('error', 100, "Gagal memproses gambar.", "Need at least 2 valid documents with extractable text.", True)
                return
                
            update_status('processing', 60, "Membandingkan kemiripan dokumen...")
            results = compare_all_pairs(documents)
            
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
