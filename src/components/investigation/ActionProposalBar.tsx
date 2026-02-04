import { ThumbsUp, ThumbsDown, Edit3 } from 'lucide-react';
import { Button } from '../common';
import { cn } from '../../lib/utils';

interface ActionProposalProps {
  title: string;
  confidence: number;
  description: string;
  onApprove: () => void;
  onReject: () => void;
  onEdit: () => void;
  canApprove: boolean;
}

export default function ActionProposalBar({
  title,
  confidence,
  description,
  onApprove,
  onReject,
  onEdit,
  canApprove,
}: ActionProposalProps) {
  return (
    <div className="p-4 border-t border-primary bg-bg-surface">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm text-text-main font-medium">
            建议操作: {title}
          </p>
          <p className="text-xs text-text-muted mt-1">
            置信度 {confidence}% - 基于日志分析和配置审查
          </p>
        </div>
        <div className="flex items-center gap-2">
          {canApprove ? (
            <>
              <Button onClick={onApprove} variant="success" icon={<ThumbsUp className="w-4 h-4" />}>
                批准
              </Button>
              <Button onClick={onEdit} variant="secondary" icon={<Edit3 className="w-4 h-4" />}>
                编辑
              </Button>
              <Button onClick={onReject} variant="danger" icon={<ThumbsDown className="w-4 h-4" />}>
                拒绝
              </Button>
            </>
          ) : (
            <span className="text-sm text-semantic-warning">
              需要工程师或管理员权限才能操作
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
