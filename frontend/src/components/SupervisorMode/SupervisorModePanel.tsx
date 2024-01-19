import { CommandBarButton, ContextualMenu, DefaultButton, Dialog, DialogFooter, DialogType, ICommandBarStyles, IContextualMenuItem, IStackStyles, PrimaryButton, Spinner, SpinnerSize, Stack, StackItem, Text, Separator } from "@fluentui/react";
import { useBoolean } from '@fluentui/react-hooks';
import { LtiConfig } from '../../api/models';
import styles from "./SupervisorModePanel.module.css"
import { useContext } from "react";
import { WelcomeMessageItem } from "./WelcomeMessageItem";
import { SystemMessageItem } from "./SystemMessageItem";
import { AppStateContext } from "../../state/AppProvider";
import React from "react";
// import ChatHistoryList from "./ChatHistoryList";
// import { SupervisorModeLoadingState, historyDeleteAll } from "../../api";

interface SupervisorModePanelProps {
    
}

export enum SupervisorModePanelTabs {
    History = "History"
}

const commandBarStyle: ICommandBarStyles = {
    root: {
        padding: '0',
        display: 'flex',
        justifyContent: 'center',
        backgroundColor: 'transparent'
    },
};

const commandBarButtonStyle: Partial<IStackStyles> = { root: { height: '50px' } };

export function SupervisorModePanel(props: SupervisorModePanelProps) {
    const appStateContext = useContext(AppStateContext)
    const [showContextualMenu, setShowContextualMenu] = React.useState(false);
    const [hideClearAllDialog, { toggle: toggleClearAllDialog }] = useBoolean(true);
    const [clearing, setClearing] = React.useState(false)
    const [clearingError, setClearingError] = React.useState(false)
    
    const config = appStateContext?.state.ltiConfig;
    

    
    // const clearAllDialogContentProps = {
    //     type: DialogType.close,
    //     title: !clearingError? 'Are you sure you want to clear all chat history?' : 'Error deleting all of chat history',
    //     closeButtonAriaLabel: 'Close',
    //     subText: !clearingError ? 'All chat history will be permanently removed.' : 'Please try again. If the problem persists, please contact the site administrator.',
    // };
    
//     const modalProps = {
//         titleAriaId: 'labelId',
//         subtitleAriaId: 'subTextId',
//         isBlocking: true,
//         styles: { main: { maxWidth: 450 } },
//     }
// 
//     const menuItems: IContextualMenuItem[] = [
//         { key: 'clearAll', text: 'Clear all chat history', iconProps: { iconName: 'Delete' }},
//     ];

    const handleHistoryClick = () => {
        appStateContext?.dispatch({ type: 'TOGGLE_SUPERVISOR_MODE' })
    };
    
    // const onShowContextualMenu = React.useCallback((ev: React.MouseEvent<HTMLElement>) => {
    //     ev.preventDefault(); // don't navigate
    //     setShowContextualMenu(true);
    // }, []);

    // const onHideContextualMenu = React.useCallback(() => setShowContextualMenu(false), []);

    // const onClearAllChatHistory = async () => {
    //     setClearing(true)
    //     let response = await historyDeleteAll()
    //     if(!response.ok){
    //         setClearingError(true)
    //     }else{
    //         appStateContext?.dispatch({ type: 'DELETE_CHAT_HISTORY' })
    //         toggleClearAllDialog();
    //     }
    //     setClearing(false);
    // }

    // const onHideClearAllDialog = () => {
    //     toggleClearAllDialog()
    //     setTimeout(() => {
    //         setClearingError(false)
    //     }, 2000);
    // }

    // React.useEffect(() => {}, [appStateContext?.state.chatHistory, clearingError]);

    return (
        <section className={styles.container} data-is-scrollable aria-label={"supervisor mode panel"}>
            <Stack horizontal horizontalAlign='space-between' verticalAlign='center' wrap aria-label="supervisor mode header">
                <StackItem>
                    <Text role="heading" aria-level={2} style={{ alignSelf: "center", fontWeight: "600", fontSize: "18px", marginRight: "auto", paddingLeft: "20px" }}>Supervisor Panel</Text>
                  
                </StackItem>
                

                
                <Stack verticalAlign="start">
                    <Stack horizontal styles={commandBarButtonStyle}>
                        <CommandBarButton
                            iconProps={{ iconName: 'Cancel' }}
                            title={"Hide"}
                            onClick={handleHistoryClick}
                            aria-label={"hide button"}
                            styles={commandBarStyle}
                            role="button"
                        />
                    </Stack>
                </Stack>
            </Stack>
            <Stack aria-label="supervisor panel content"
                styles={{
                    root: {
                        display: "flex",
                        flexGrow: 1,
                        flexDirection: "column",
                        paddingTop: '2.5px',
                        maxWidth: "100%"
                    },
                }}
                style={{
                    display: "flex",
                    flexGrow: 1,
                    flexDirection: "column",
                    flexWrap: "wrap",
                    padding: "1px"
                }}>
                <div className={styles.listContainer}>
                    {
                        <Stack horizontalAlign="start" verticalAlign="center" className={styles.chatGroup} aria-label={`supervisor option group`}>
                            <Stack aria-label="supervisor panel hint" className={styles.hintTitle}>
                                <p>You can try out new settings for the chat bot. Your changes only affect your personal instance of the chatbot until you click "Publish". </p>
                            <p>
                            Once published, your new settings will apply to all students in the course. 
                            </p>
                            <p>
                            You can click "Revert" to discard your changes go back to the currently published settings for the course.
                            </p>
                            </Stack>
                        
                        <Separator styles={{
                        root: {
                            width: '100%',
                            position: 'relative',
                            '::before': {
                              backgroundColor: '#d6d6d6',
                            },
                          },
                        }}/>
                        </Stack>
                    } 
                    {
                        
                    <Stack horizontalAlign="start" verticalAlign="center" className={styles.chatGroup} aria-label={`supervisor option       group`}>
                        <Stack aria-label="welcome message" className={styles.chatMonth}>Welcome Message</Stack>
                        <Stack aria-label="welcome message hint" className={styles.hintTitle}>This subtitle is displayed when a user begins a new conversation.</Stack>                    
                        <Stack horizontal verticalAlign={'center'} style={{ width: '100%' }}>                      
                          <WelcomeMessageItem itemText={config?.welcome_message}/>
                        </Stack>
                        <Separator styles={{
                        root: {
                            width: '100%',
                            position: 'relative',
                            '::before': {
                              backgroundColor: '#d6d6d6',
                            },
                          },
                        }}/>
                        <Stack aria-label="system message" className={styles.chatMonth}>System Message</Stack>
                        <Stack aria-label="system message hint" className={styles.hintTitle}>The system message defines the personality of the chat bot.</Stack>                    
                        <Stack horizontal verticalAlign={'center'} style={{ width: '100%' }}>                      
                          <SystemMessageItem itemText={config?.system_message}/>
                        </Stack>
                        <Separator styles={{
                        root: {
                            width: '100%',
                            position: 'relative',
                            '::before': {
                              backgroundColor: '#d6d6d6',
                            },
                          },
                        }}/>
                    </Stack>
                 
                        

                        
                    }
                </div>
                
            </Stack>

        </section>
    );
}