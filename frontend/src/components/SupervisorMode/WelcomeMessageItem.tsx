import * as React from 'react';
import { DefaultButton, Dialog, DialogFooter, DialogType, Text, IconButton, List, PrimaryButton, Separator, Stack, TextField, ITextField } from '@fluentui/react';

import { AppStateContext } from '../../state/AppProvider';


import styles from "./SupervisorModePanel.module.css"
import { useBoolean } from '@fluentui/react-hooks';

import { welcomeMessageRename } from '../../api';
import { useEffect, useRef, useState } from 'react';

interface WelcomeMessageItemProps {
  itemText?: string;
}


export const WelcomeMessageItem: React.FC<WelcomeMessageItemProps> = ({
  itemText
}) => {
	const [isHovered, setIsHovered] = React.useState(false);
	const [edit, setEdit] = useState(false);
	const [editTitle, setEditTitle] = useState("");
	// const [hideDeleteDialog, { toggle: toggleDeleteDialog }] = useBoolean(true);
	// const [errorDelete, setErrorDelete] = useState(false);
	const [renameLoading, setRenameLoading] = useState(false);
	const [errorRename, setErrorRename] = useState<string | undefined>(undefined);
	const [textFieldFocused, setTextFieldFocused] = useState(false);
	const textFieldRef = useRef<ITextField | null>(null);
	
	const appStateContext = React.useContext(AppStateContext)
	// const isSelected = item?.id === appStateContext?.state.currentChat?.id;


	const modalProps = {
		titleAriaId: 'labelId',
		subtitleAriaId: 'subTextId',
		isBlocking: true,
		styles: { main: { maxWidth: 450 } },
	}

	if (!itemText) {
		return null;
	}

	useEffect(() => {
		if (textFieldFocused && textFieldRef.current) {
			textFieldRef.current.focus();
			setTextFieldFocused(false);
		}
	}, [textFieldFocused]);

	// useEffect(() => {
	// 	if (appStateContext?.state.currentChat?.id !== item?.id) {
	// 		setEdit(false);
	// 		setEditTitle('')
	// 	}
	// }, [appStateContext?.state.currentChat?.id, item?.id]);

	// const onDelete = async () => {
	// 	let response = await historyDelete(item.id)
	// 	if(!response.ok){
	// 		setErrorDelete(true)
	// 		setTimeout(() => {
	// 			setErrorDelete(false);
	// 		}, 5000);
	// 	}else{
	// 		appStateContext?.dispatch({ type: 'DELETE_CHAT_ENTRY', payload: item.id })
	// 	}
	// 	toggleDeleteDialog();
	// };

	const onEdit = () => {
		setEdit(true)
		setTextFieldFocused(true)
		setEditTitle(itemText)
	};

	// const handleSelectItem = () => {
	// 	onSelect(item)
	// 	appStateContext?.dispatch({ type: 'UPDATE_CURRENT_CHAT', payload: item } )
	// }

	const truncatedTitle = ((itemText?.length ?? 0) > 140) ? `${itemText?.substring(0, 140)} ...` : itemText;

	const handleSaveEdit = async (e: any) => {
		e.preventDefault();
		if(errorRename || renameLoading){
			return;
		}
		if(editTitle == itemText){
			setErrorRename("Error: Enter a new welcome message to proceed.")
			setTimeout(() => {
				setErrorRename(undefined);
				setTextFieldFocused(true);
				if (textFieldRef.current) {
					textFieldRef.current.focus();
				}
			}, 5000);
			return
		}
		setRenameLoading(true)
		let response = await welcomeMessageRename(editTitle);
		if(!response.ok){
			setErrorRename("Error: could not update welcome message")
			setTimeout(() => {
				setTextFieldFocused(true);
				setErrorRename(undefined);
				if (textFieldRef.current) {
					textFieldRef.current.focus();
				}
			}, 5000);
		}else{
			setRenameLoading(false)
			setEdit(false)
			appStateContext?.dispatch({ type: 'UPDATE_WELCOME_MESSAGE', payload: editTitle})
			setEditTitle("");
		}
	}

	const welcomeMessageTitleOnChange = (e: any) => {
		setEditTitle(e.target.value);
	};

	const cancelEditTitle = () => {
		setEdit(false)
		setEditTitle("");
	}

	const handleKeyPressEdit = (e: any) => {
		if(e.key === "Enter"){
			return handleSaveEdit(e)
		}
		if(e.key === "Escape"){
			cancelEditTitle();
			return
		}
	}

	return (
		<Stack
			
			tabIndex={0}
			aria-label='welcome message item'
			className={styles.itemCell}
			
			
			verticalAlign='center'
			// horizontal
			onMouseEnter={() => setIsHovered(true)}
			onMouseLeave={() => setIsHovered(false)}
			
		>
			{edit ? <>
				<Stack.Item 
					style={{ width: '100%' }}
				>
					<form aria-label='edit welcome message form' onSubmit={(e) => handleSaveEdit(e)} style={{padding: '5px 0px'}}>
						<Stack horizontal verticalAlign={'start'}>
							<Stack.Item>
								<TextField
									componentRef={textFieldRef}
									autoFocus={textFieldFocused}
									className={styles.welcomeMessageInputTextArea}
									placeholder={itemText}
									multiline
									autoAdjustHeight
									borderless
									value={editTitle}
									onChange={welcomeMessageTitleOnChange}
									onKeyDown={handleKeyPressEdit}
									disabled={errorRename ? true : false}
								/>
							</Stack.Item>
							{editTitle && (<Stack.Item>
								<Stack aria-label='action button group' horizontal verticalAlign={'center'}>
									<IconButton role='button' disabled={errorRename !== undefined} onKeyDown={e => e.key === " " || e.key === 'Enter' ? handleSaveEdit(e) : null} onClick={(e) => handleSaveEdit(e)} aria-label='confirm new welcome message' iconProps={{iconName: 'CheckMark'}} styles={{ root: { color: 'green', marginLeft: '5px' } }} />
									<IconButton role='button' disabled={errorRename !== undefined} onKeyDown={e => e.key === " " || e.key === 'Enter' ? cancelEditTitle() : null} onClick={() => cancelEditTitle()} aria-label='cancel edit welcome message' iconProps={{iconName: 'Cancel'}} styles={{ root: { color: 'red', marginLeft: '5px' } }} />
								</Stack>
							</Stack.Item>)}
						</Stack>
						{errorRename && (
							<Text role='alert' aria-label={errorRename} style={{fontSize: 12, fontWeight: 400, color: 'rgb(164,38,44)'}}>{errorRename}</Text>
						)}
					</form>
				</Stack.Item>
			</> : <>
				<Stack horizontal verticalAlign={'center'} style={{ width: '100%' }}>
					<div className={styles.chatTitle} onClick={onEdit}>{truncatedTitle}</div>
					{(isHovered) && <Stack horizontal horizontalAlign='end'>					
						<IconButton className={styles.itemButton} iconProps={{ iconName: 'Edit' }} title="Edit" onClick={onEdit} onKeyDown={e => e.key === " " ? onEdit() : null}/>
					</Stack>}
				</Stack>
			</>
			}
		</Stack>
	);
};
